from __future__ import annotations

from dataclasses import dataclass

import torch

from holosoma.simulator.mjlab.mjlab_simulator import MJLab


@dataclass
class _EntityRecorder:
    ctrl: torch.Tensor | None = None

    def write_ctrl_to_sim(self, ctrl: torch.Tensor) -> None:
        self.ctrl = ctrl.clone()


def _build_simulator(num_envs: int = 2, num_dof: int = 3, num_bodies: int = 4) -> MJLab:
    sim = object.__new__(MJLab)
    sim.device = "cpu"
    sim.sim_device = "cpu"
    sim.num_envs = num_envs
    sim.num_dof = num_dof
    sim.num_bodies = num_bodies
    sim.dof_names = [f"joint_{i}" for i in range(num_dof)]
    sim.body_names = [f"body_{i}" for i in range(num_bodies)]
    sim._body_name_to_index = {name: i for i, name in enumerate(sim.body_names)}
    sim.dof_pos = torch.zeros((num_envs, num_dof))
    sim.dof_vel = torch.zeros((num_envs, num_dof))
    sim.dof_state = torch.zeros((num_envs, num_dof, 2))
    sim.robot_root_states = torch.zeros((num_envs, 13))
    sim.all_root_states = sim.robot_root_states.clone()
    sim.contact_forces = torch.zeros((num_envs, num_bodies, 3))
    sim.contact_forces_history = torch.zeros((num_envs, 2, num_bodies, 3))
    sim._entity = _EntityRecorder()
    sim._sim_time = 0.25
    sim._pending_position_targets = None
    sim._pending_velocity_targets = None
    sim._pending_effort_targets = None
    sim._pending_bridge_effort = None
    return sim


def test_interface_runtime_tensors_and_core_apis() -> None:
    sim = _build_simulator()

    assert sim.dof_state.shape == (2, 3, 2)
    assert sim.dof_pos.shape == (2, 3)
    assert sim.dof_vel.shape == (2, 3)
    assert sim.robot_root_states.shape == (2, 13)
    assert sim.all_root_states.shape == (2, 13)
    assert sim.contact_forces.shape == (2, 4, 3)

    new_root = torch.randn(2, 13)
    sim.set_actor_root_state_tensor_robots(torch.tensor([0, 1]), new_root)
    assert torch.allclose(sim.robot_root_states, new_root)
    assert torch.allclose(sim.all_root_states, new_root)

    dof_states = torch.randn(2, 3, 2)
    sim.set_dof_state_tensor_robots(torch.tensor([0, 1]), dof_states)
    assert torch.allclose(sim.dof_state, dof_states)
    assert torch.allclose(sim.dof_pos, dof_states[..., 0])
    assert torch.allclose(sim.dof_vel, dof_states[..., 1])

    assert sim.find_rigid_body_indice("body_2") == 2

    sim.contact_forces_history[:] = 1.0
    sim.clear_contact_forces_history(torch.tensor([1]))
    assert torch.allclose(sim.contact_forces_history[1], torch.zeros_like(sim.contact_forces_history[1]))
    assert torch.all(sim.contact_forces_history[0] == 1.0)

    torques = torch.randn(2, 3)
    sim.apply_torques_at_dof(torques)
    assert sim._entity.ctrl is not None
    assert torch.allclose(sim._entity.ctrl, torques)

    assert sim.time() == 0.25

