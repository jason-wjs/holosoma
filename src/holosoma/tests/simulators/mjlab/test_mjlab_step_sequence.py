from __future__ import annotations

import torch

from holosoma.simulator.mjlab.mjlab_simulator import MJLab


class _EntityRecorder:
    def __init__(self, events: list[str]):
        self.events = events
        self.position_targets: torch.Tensor | None = None
        self.velocity_targets: torch.Tensor | None = None
        self.effort_targets: torch.Tensor | None = None
        self.ctrl: torch.Tensor | None = None

    def set_joint_position_target(self, targets: torch.Tensor) -> None:
        self.position_targets = targets.clone()
        self.events.append("entity:set_joint_position_target")

    def set_joint_velocity_target(self, targets: torch.Tensor) -> None:
        self.velocity_targets = targets.clone()
        self.events.append("entity:set_joint_velocity_target")

    def set_joint_effort_target(self, targets: torch.Tensor) -> None:
        self.effort_targets = targets.clone()
        self.events.append("entity:set_joint_effort_target")

    def write_ctrl_to_sim(self, torques: torch.Tensor) -> None:
        self.ctrl = torques.clone()
        self.events.append("entity:write_ctrl_to_sim")


class _SceneRecorder:
    def __init__(self, events: list[str]):
        self.events = events

    def write_data_to_sim(self) -> None:
        self.events.append("scene:write_data_to_sim")

    def update(self, dt: float) -> None:
        self.events.append(f"scene:update:{dt}")


class _SimRecorder:
    def __init__(self, events: list[str]):
        self.events = events

    def step(self) -> None:
        self.events.append("sim:step")


def _build_simulator() -> tuple[MJLab, list[str], _EntityRecorder]:
    events: list[str] = []
    entity = _EntityRecorder(events)
    sim = object.__new__(MJLab)
    sim.device = "cpu"
    sim.sim_device = "cpu"
    sim.num_envs = 2
    sim.num_dof = 3
    sim.dof_pos = torch.zeros((2, 3))
    sim.dof_vel = torch.zeros((2, 3))
    sim.sim_dt = 0.005
    sim._scene = _SceneRecorder(events)
    sim._sim = _SimRecorder(events)
    sim._entity = entity
    sim._pending_position_targets = None
    sim._pending_velocity_targets = None
    sim._pending_effort_targets = None
    sim._pending_bridge_effort = None
    sim._step_bridge = lambda: events.append("bridge:step")
    sim.refresh_sim_tensors = lambda: events.append("sim:refresh")
    sim._video_recorder = None
    sim.video_recorder = None
    sim.virtual_gantry = None
    sim.simulator_config = type("Cfg", (), {"sim": type("SimCfg", (), {"fps": 200})})()
    return sim, events, entity


def test_step_sequence_applies_targets_before_step() -> None:
    sim, events, entity = _build_simulator()

    sim.queue_dof_position_targets(torch.ones((2, 3)))
    sim.queue_dof_velocity_targets(torch.full((2, 3), 2.0))
    sim.queue_dof_effort_targets(torch.full((2, 3), 3.0))
    sim.simulate_at_each_physics_step()

    assert events == [
        "bridge:step",
        "entity:set_joint_position_target",
        "entity:set_joint_velocity_target",
        "entity:set_joint_effort_target",
        "scene:write_data_to_sim",
        "sim:step",
        "scene:update:0.005",
        "sim:refresh",
    ]
    assert entity.position_targets is not None
    assert entity.velocity_targets is not None
    assert entity.effort_targets is not None


def test_bridge_torque_overrides_targets_for_step() -> None:
    sim, events, entity = _build_simulator()

    sim.queue_dof_position_targets(torch.ones((2, 3)))
    bridge_torques = torch.full((2, 3), 7.0)
    sim.apply_torques_at_dof(bridge_torques)
    sim.simulate_at_each_physics_step()

    assert "entity:set_joint_position_target" not in events
    assert "entity:write_ctrl_to_sim" in events
    assert entity.ctrl is not None
    assert torch.allclose(entity.ctrl, bridge_torques)

