"""MJLAB simulator backend implementation."""

from __future__ import annotations

from typing import Any

from loguru import logger

from holosoma.config_types.full_sim import FullSimConfig
from holosoma.managers.terrain.manager import TerrainManager
from holosoma.simulator.base_simulator.base_simulator import BaseSimulator
from holosoma.simulator.mjlab.entity_adapter import build_entity_cfg
from holosoma.simulator.mjlab.state_adapter import (
    quat_wxyz_to_xyzw,
    root_state_holosoma_to_mjlab,
)
from holosoma.simulator.shared.object_registry import ObjectType
from holosoma.utils.safe_torch_import import torch

try:
    from mjlab.scene.scene import Scene, SceneCfg
    from mjlab.sim.sim import Simulation, SimulationCfg
except ImportError:  # pragma: no cover - exercised in non-mjlab environments
    Scene = None
    SceneCfg = None
    Simulation = None
    SimulationCfg = None


class MJLab(BaseSimulator):
    """MJLAB simulator backend with target-buffer control semantics."""

    def __init__(self, tyro_config: FullSimConfig, terrain_manager: TerrainManager, device: str) -> None:
        super().__init__(tyro_config, terrain_manager, device)
        self.tyro_config = tyro_config
        self.device = device
        self.sim_device = device
        self.num_envs = self.training_config.num_envs
        self.sim_dt = 1.0 / float(self.simulator_config.sim.fps)
        self.viewer = None

        self._scene: Any | None = None
        self._sim: Any | None = None
        self._entity: Any | None = None
        self._contact_sensor: Any | None = None
        self._contact_slot_to_body_index: list[int] = []

        self._sim_time: float = 0.0
        self._body_name_to_index: dict[str, int] = {}

        self._pending_position_targets: torch.Tensor | None = None
        self._pending_velocity_targets: torch.Tensor | None = None
        self._pending_effort_targets: torch.Tensor | None = None
        self._pending_bridge_effort: torch.Tensor | None = None

        self.num_dof = 0
        self.num_bodies = 0
        self.dof_names: list[str] = []
        self.body_names: list[str] = []

        self.dof_pos = torch.zeros((self.num_envs, 0), dtype=torch.float32, device=self.device)
        self.dof_vel = torch.zeros_like(self.dof_pos)
        self.dof_state = torch.zeros((self.num_envs, 0, 2), dtype=torch.float32, device=self.device)
        self.robot_root_states = torch.zeros((self.num_envs, 13), dtype=torch.float32, device=self.device)
        self.all_root_states = self.robot_root_states.clone()
        self.base_quat = self.robot_root_states[:, 3:7]
        self.contact_forces = torch.zeros((self.num_envs, 0, 3), dtype=torch.float32, device=self.device)
        self.contact_forces_history = torch.zeros((self.num_envs, 1, 0, 3), dtype=torch.float32, device=self.device)

        self._rigid_body_pos = torch.zeros((self.num_envs, 0, 3), dtype=torch.float32, device=self.device)
        self._rigid_body_rot = torch.zeros((self.num_envs, 0, 4), dtype=torch.float32, device=self.device)
        self._rigid_body_vel = torch.zeros((self.num_envs, 0, 3), dtype=torch.float32, device=self.device)
        self._rigid_body_ang_vel = torch.zeros((self.num_envs, 0, 3), dtype=torch.float32, device=self.device)

    def setup(self):
        return

    def setup_terrain(self):
        return

    def get_supported_scene_formats(self):
        return ["xml", "mjcf"]

    def load_assets(self):
        if Scene is None or SceneCfg is None or Simulation is None or SimulationCfg is None:
            raise ImportError(
                "MJLab backend requires mjlab==1.1.1 to be installed. "
                "Use scripts/setup_mjlab.sh and run in the hsmjlab environment."
            )

        entity_cfg = build_entity_cfg(self.robot_config)
        scene_cfg = SceneCfg(
            num_envs=self.num_envs,
            entities={"robot": entity_cfg},
        )
        self._scene = Scene(scene_cfg, device=self.device)
        model = self._scene.compile()
        self._sim = Simulation(num_envs=self.num_envs, cfg=SimulationCfg(), model=model, device=self.device)
        self._scene.initialize(model, self._sim.wp_model, self._sim.wp_data)

        self._entity = self._scene.entities["robot"]
        self.dof_names = list(self._entity.joint_names)
        self.body_names = list(self._entity.body_names)
        self.num_dof = len(self.dof_names)
        self.num_bodies = len(self.body_names)
        self._body_name_to_index = {name: i for i, name in enumerate(self.body_names)}
        self._contact_slot_to_body_index = list(range(self.num_bodies))

        self.dof_pos = torch.zeros((self.num_envs, self.num_dof), dtype=torch.float32, device=self.device)
        self.dof_vel = torch.zeros_like(self.dof_pos)
        self.dof_state = torch.zeros((self.num_envs, self.num_dof, 2), dtype=torch.float32, device=self.device)
        self.contact_forces = torch.zeros((self.num_envs, self.num_bodies, 3), dtype=torch.float32, device=self.device)
        hist_len = max(1, int(self.simulator_config.contact_sensor_history_length))
        self.contact_forces_history = torch.zeros(
            (self.num_envs, hist_len, self.num_bodies, 3), dtype=torch.float32, device=self.device
        )
        self._rigid_body_pos = torch.zeros((self.num_envs, self.num_bodies, 3), dtype=torch.float32, device=self.device)
        self._rigid_body_rot = torch.zeros((self.num_envs, self.num_bodies, 4), dtype=torch.float32, device=self.device)
        self._rigid_body_vel = torch.zeros((self.num_envs, self.num_bodies, 3), dtype=torch.float32, device=self.device)
        self._rigid_body_ang_vel = torch.zeros(
            (self.num_envs, self.num_bodies, 3), dtype=torch.float32, device=self.device
        )

    def create_envs(self, num_envs, env_origins, base_init_state, env_config=None):
        del env_config
        self.num_envs = int(num_envs)

        if self._entity is None:
            return

        root_states = base_init_state.to(device=self.device, dtype=torch.float32).repeat(self.num_envs, 1)
        root_states[:, :3] += env_origins.to(device=self.device, dtype=torch.float32)
        self.robot_root_states = root_states
        self.all_root_states = self.robot_root_states.clone()
        self.base_quat = self.robot_root_states[:, 3:7]

        default_joint_pos = torch.zeros((self.num_envs, self.num_dof), dtype=torch.float32, device=self.device)
        for i, dof_name in enumerate(self.dof_names):
            default_joint_pos[:, i] = float(self.robot_config.init_state.default_joint_angles[dof_name])
        self.dof_pos = default_joint_pos
        self.dof_vel = torch.zeros_like(self.dof_pos)
        self.dof_state = torch.stack((self.dof_pos, self.dof_vel), dim=-1)

        self._entity.write_root_state_to_sim(root_state_holosoma_to_mjlab(self.robot_root_states))
        self._entity.write_joint_state_to_sim(self.dof_pos, self.dof_vel)
        self._sim.forward()
        self.refresh_sim_tensors()

    def get_dof_limits_properties(self):
        self.hard_dof_pos_limits = torch.zeros((self.num_dof, 2), dtype=torch.float32, device=self.device)
        self.dof_pos_limits = torch.zeros_like(self.hard_dof_pos_limits)
        self.dof_vel_limits = torch.zeros((self.num_dof,), dtype=torch.float32, device=self.device)
        self.torque_limits = torch.zeros((self.num_dof,), dtype=torch.float32, device=self.device)

        for i in range(self.num_dof):
            self.hard_dof_pos_limits[i, 0] = self.robot_config.dof_pos_lower_limit_list[i]
            self.hard_dof_pos_limits[i, 1] = self.robot_config.dof_pos_upper_limit_list[i]
            self.dof_pos_limits[i, 0] = self.robot_config.dof_pos_lower_limit_list[i]
            self.dof_pos_limits[i, 1] = self.robot_config.dof_pos_upper_limit_list[i]
            self.dof_vel_limits[i] = self.robot_config.dof_vel_limit_list[i]
            self.torque_limits[i] = self.robot_config.dof_effort_limit_list[i]

            midpoint = (self.dof_pos_limits[i, 0] + self.dof_pos_limits[i, 1]) / 2
            span = self.dof_pos_limits[i, 1] - self.dof_pos_limits[i, 0]
            self.dof_pos_limits[i, 0] = midpoint - 0.5 * span * self.robot_config.soft_dof_pos_limit
            self.dof_pos_limits[i, 1] = midpoint + 0.5 * span * self.robot_config.soft_dof_pos_limit

        return self.dof_pos_limits, self.dof_vel_limits, self.torque_limits

    def find_rigid_body_indice(self, body_name):
        return self._body_name_to_index[body_name]

    def prepare_sim(self):
        if self._entity is None:
            return

        self.object_registry.setup_ranges(self.num_envs, robot_count=1, scene_count=0, individual_count=0)
        initial_poses = self.robot_root_states[:, :7].clone()
        self.object_registry.register_object("robot", ObjectType.ROBOT, 0, initial_poses=initial_poses)
        self.object_registry.finalize_registration()
        self.refresh_sim_tensors()

    def refresh_sim_tensors(self):
        if self._entity is None:
            return

        self.dof_pos = self._entity.data.joint_pos.clone()
        self.dof_vel = self._entity.data.joint_vel.clone()
        self.dof_state = torch.stack((self.dof_pos, self.dof_vel), dim=-1)

        root_pose_wxyz = self._entity.data.root_link_pose_w
        root_vel = self._entity.data.root_link_vel_w
        root_pose_xyzw = root_pose_wxyz.clone()
        root_pose_xyzw[:, 3:7] = quat_wxyz_to_xyzw(root_pose_wxyz[:, 3:7])
        self.robot_root_states = torch.cat((root_pose_xyzw, root_vel), dim=-1)
        self.all_root_states = self.robot_root_states.clone()
        self.base_quat = self.robot_root_states[:, 3:7]

        self._rigid_body_pos = self._entity.data.body_link_pos_w.clone()
        body_quat_wxyz = self._entity.data.body_link_quat_w.clone()
        self._rigid_body_rot = quat_wxyz_to_xyzw(body_quat_wxyz)
        self._rigid_body_vel = self._entity.data.body_link_lin_vel_w.clone()
        self._rigid_body_ang_vel = self._entity.data.body_link_ang_vel_w.clone()

        if self.contact_forces.numel() > 0:
            self._update_contact_forces_from_sensor()
            self.contact_forces_history = torch.cat(
                [self.contact_forces.unsqueeze(1), self.contact_forces_history[:, :-1, :, :]], dim=1
            )

    def clear_contact_forces_history(self, env_id):
        idx = self._to_env_ids(env_id)
        if isinstance(idx, slice):
            self.contact_forces_history[:] = 0.0
            return
        if idx.numel() > 0:
            self.contact_forces_history[idx, :, :, :] = 0.0

    def queue_dof_position_targets(self, targets: torch.Tensor) -> None:
        self._pending_position_targets = targets.clone()

    def queue_dof_velocity_targets(self, targets: torch.Tensor) -> None:
        self._pending_velocity_targets = targets.clone()

    def queue_dof_effort_targets(self, targets: torch.Tensor) -> None:
        self._pending_effort_targets = targets.clone()

    def apply_torques_at_dof(self, torques):
        if self._entity is not None:
            self._entity.write_ctrl_to_sim(torques)
        self._pending_bridge_effort = torques.clone()

    def simulate_at_each_physics_step(self):
        if self.virtual_gantry:
            self.virtual_gantry.step()

        self._step_bridge()

        if self._pending_bridge_effort is not None:
            if self._entity is not None:
                self._entity.write_ctrl_to_sim(self._pending_bridge_effort)
            self._pending_bridge_effort = None
            self._pending_position_targets = None
            self._pending_velocity_targets = None
            self._pending_effort_targets = None
        elif self._entity is not None:
            if self._pending_position_targets is not None:
                self._entity.set_joint_position_target(self._pending_position_targets)
                self._pending_position_targets = None
            if self._pending_velocity_targets is not None:
                self._entity.set_joint_velocity_target(self._pending_velocity_targets)
                self._pending_velocity_targets = None
            if self._pending_effort_targets is not None:
                self._entity.set_joint_effort_target(self._pending_effort_targets)
                self._pending_effort_targets = None

        if self._scene is not None:
            self._scene.write_data_to_sim()
        if self._sim is not None:
            self._sim.step()
        if self._scene is not None:
            self._scene.update(dt=self.sim_dt)

        self._sim_time = float(getattr(self, "_sim_time", 0.0) + self.sim_dt)
        self.refresh_sim_tensors()

        if self.video_recorder and self.video_recorder.is_recording:
            self.capture_video_frame()

    def setup_viewer(self):
        logger.info("MJLAB viewer integration is not implemented yet; running without interactive viewer.")
        self.viewer = None

    def render(self, sync_frame_time=True):
        del sync_frame_time
        return

    def time(self) -> float:
        return float(self._sim_time)

    def get_dof_forces(self, env_id: int = 0) -> torch.Tensor:
        if self._entity is None:
            return torch.zeros((self.num_dof,), dtype=torch.float32, device=self.device)
        return self._entity.data.actuator_force[env_id].clone()

    def configure_contact_force_mapping(self, slot_body_names: list[str]) -> None:
        """Set deterministic mapping from contact-sensor slots to robot body indices."""
        self._contact_slot_to_body_index = [self.find_rigid_body_indice(name) for name in slot_body_names]

    def _update_contact_forces_from_sensor(self) -> None:
        self.contact_forces[:] = 0.0

        if self._contact_sensor is None:
            return

        sensor_data = getattr(self._contact_sensor, "data", None)
        slot_forces = getattr(sensor_data, "force", None)
        if slot_forces is None:
            return

        slot_forces_tensor = torch.as_tensor(slot_forces, device=self.device, dtype=self.contact_forces.dtype)
        if slot_forces_tensor.dim() != 3:
            return

        num_slots = min(slot_forces_tensor.shape[1], len(self._contact_slot_to_body_index))
        for slot_idx in range(num_slots):
            body_idx = int(self._contact_slot_to_body_index[slot_idx])
            if 0 <= body_idx < self.contact_forces.shape[1]:
                self.contact_forces[:, body_idx, :] += slot_forces_tensor[:, slot_idx, :]

    def set_actor_root_state_tensor_robots(
        self, env_ids=None, root_states: torch.Tensor | None = None
    ) -> None:
        idx = self._to_env_ids(env_ids)
        source = self.robot_root_states if root_states is None else root_states
        source = self._slice_for_env_ids(source, idx)

        self.robot_root_states[idx] = source
        self.all_root_states[idx] = source

        if self._entity is not None and hasattr(self._entity, "write_root_state_to_sim"):
            self._entity.write_root_state_to_sim(root_state_holosoma_to_mjlab(source), env_ids=idx)

    def set_dof_state_tensor_robots(self, env_ids=None, dof_states: torch.Tensor | None = None) -> None:
        idx = self._to_env_ids(env_ids)
        source = self.dof_state if dof_states is None else dof_states
        if source.dim() == 2:
            source = source.view(self.num_envs, self.num_dof, 2)
        source = self._slice_for_env_ids(source, idx)

        self.dof_state[idx] = source
        self.dof_pos[idx] = source[..., 0]
        self.dof_vel[idx] = source[..., 1]

        if self._entity is not None and hasattr(self._entity, "write_joint_state_to_sim"):
            self._entity.write_joint_state_to_sim(source[..., 0], source[..., 1], env_ids=idx)

    def _to_env_ids(self, env_ids):
        if env_ids is None:
            return slice(None)
        if isinstance(env_ids, slice):
            return env_ids
        if isinstance(env_ids, int):
            return torch.tensor([env_ids], dtype=torch.long, device=self.device)
        if isinstance(env_ids, list):
            return torch.tensor(env_ids, dtype=torch.long, device=self.device)
        if isinstance(env_ids, torch.Tensor):
            return env_ids.to(device=self.device, dtype=torch.long)
        return torch.as_tensor(env_ids, device=self.device, dtype=torch.long)

    def _slice_for_env_ids(self, tensor: torch.Tensor, env_ids) -> torch.Tensor:
        if isinstance(env_ids, slice):
            return tensor
        if tensor.shape[0] == self.num_envs:
            return tensor[env_ids]
        return tensor
