from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import torch

from holosoma.config_types.action import ActionTermCfg
from holosoma.managers.action.terms.joint_control_mjlab import JointTargetActionTermMJLab


@dataclass
class _ControlCfg:
    control_type: str
    clip_actions: bool = False
    action_clip_value: float = 1.0
    clip_torques: bool = True
    action_scale: float = 0.5
    action_scales_by_effort_limit_over_p_gain: bool = False
    stiffness: dict[str, float] | None = None
    damping: dict[str, float] | None = None
    integral: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if self.stiffness is None:
            self.stiffness = {"joint": 10.0}
        if self.damping is None:
            self.damping = {"joint": 1.0}
        if self.integral is None:
            self.integral = {}


class _DummySimulator:
    def __init__(self, num_envs: int, num_dof: int, device: str):
        self.device = device
        self.dof_pos = torch.zeros((num_envs, num_dof), device=device)
        self.dof_vel = torch.zeros((num_envs, num_dof), device=device)
        self.position_targets: torch.Tensor | None = None
        self.velocity_targets: torch.Tensor | None = None
        self.effort_targets: torch.Tensor | None = None
        self.apply_torques_called = False

    def queue_dof_position_targets(self, targets: torch.Tensor) -> None:
        self.position_targets = targets.clone()

    def queue_dof_velocity_targets(self, targets: torch.Tensor) -> None:
        self.velocity_targets = targets.clone()

    def queue_dof_effort_targets(self, targets: torch.Tensor) -> None:
        self.effort_targets = targets.clone()

    def apply_torques_at_dof(self, torques: torch.Tensor) -> None:
        self.apply_torques_called = True

    def __getattr__(self, name: str):
        if name in {"_entity", "entity", "scene"}:
            raise AssertionError(f"Unexpected low-level simulator access: {name}")
        raise AttributeError(name)


class _DummyEnv:
    def __init__(self, control_type: str, num_envs: int = 2, num_dof: int = 3):
        self.device = "cpu"
        self.num_envs = num_envs
        self.num_dof = num_dof
        self.dof_names = [f"joint_{i}" for i in range(num_dof)]
        self.sim_dt = 0.005
        self.default_dof_pos = torch.full((num_envs, num_dof), 0.1)
        self.torque_limits = torch.full((num_dof,), 1.0)
        self.log_dict: dict[str, torch.Tensor] = {}
        self._randomize_ctrl_delay = False
        self._pending_torque_rfi = (False, 0.0)
        self.action_delay_idx = torch.zeros((num_envs,), dtype=torch.long)
        self.simulator = _DummySimulator(num_envs=num_envs, num_dof=num_dof, device=self.device)
        self.robot_config = SimpleNamespace(
            control=_ControlCfg(control_type=control_type),
            init_state=SimpleNamespace(default_joint_angles={name: 0.0 for name in self.dof_names}),
            dof_effort_limit_list=[1.0 for _ in range(num_dof)],
        )


def _build_term(env: _DummyEnv) -> JointTargetActionTermMJLab:
    cfg = ActionTermCfg(
        func="holosoma.managers.action.terms.joint_control_mjlab:JointTargetActionTermMJLab",
        params={},
        scale=1.0,
        clip=None,
    )
    return JointTargetActionTermMJLab(cfg, env)


def test_position_control_writes_position_targets() -> None:
    env = _DummyEnv(control_type="P")
    term = _build_term(env)

    actions = torch.full((env.num_envs, env.num_dof), 0.2)
    term.process_actions(actions)
    term.apply_actions()

    expected = actions * env.robot_config.control.action_scale + env.default_dof_pos
    assert env.simulator.position_targets is not None
    assert torch.allclose(env.simulator.position_targets, expected)
    assert env.simulator.velocity_targets is None
    assert env.simulator.effort_targets is None
    assert not env.simulator.apply_torques_called


def test_velocity_control_writes_velocity_targets() -> None:
    env = _DummyEnv(control_type="V")
    term = _build_term(env)

    actions = torch.full((env.num_envs, env.num_dof), 0.2)
    term.process_actions(actions)
    term.apply_actions()

    expected = actions * env.robot_config.control.action_scale
    assert env.simulator.velocity_targets is not None
    assert torch.allclose(env.simulator.velocity_targets, expected)
    assert env.simulator.position_targets is None
    assert env.simulator.effort_targets is None
    assert not env.simulator.apply_torques_called


def test_torque_control_writes_effort_targets() -> None:
    env = _DummyEnv(control_type="T")
    term = _build_term(env)

    actions = torch.full((env.num_envs, env.num_dof), 0.4)
    term.process_actions(actions)
    term.apply_actions()

    expected = torch.full((env.num_envs, env.num_dof), 0.2)
    assert env.simulator.effort_targets is not None
    assert torch.allclose(env.simulator.effort_targets, expected)
    assert env.simulator.position_targets is None
    assert env.simulator.velocity_targets is None
    assert not env.simulator.apply_torques_called


def test_actuator_randomization_hooks_remain_available() -> None:
    env = _DummyEnv(control_type="P")
    term = _build_term(env)

    kp_scale = torch.full((env.num_envs, env.num_dof), 1.1)
    kd_scale = torch.full((env.num_envs, env.num_dof), 0.9)
    rfi_scale = torch.full((env.num_envs, env.num_dof), 1.2)

    term.attach_actuator_scales(kp_scale, kd_scale, rfi_scale)
    kp_ref, kd_ref = term.get_pd_scale_tensors()
    assert kp_ref is kp_scale
    assert kd_ref is kd_scale
    assert term.get_rfi_scale_tensor() is rfi_scale

    term.configure_torque_rfi(enabled=True, rfi_lim=0.2)
    assert term._randomize_torque_rfi is True
    assert term._rfi_lim == 0.2
