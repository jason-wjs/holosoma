from __future__ import annotations

from types import SimpleNamespace

import torch

from holosoma.simulator.mjlab.mjlab_simulator import MJLab


def _build_simulator() -> MJLab:
    sim = object.__new__(MJLab)
    sim.device = "cpu"
    sim.num_envs = 2
    sim.body_names = ["pelvis", "left_foot", "right_foot"]
    sim.num_bodies = len(sim.body_names)
    sim._body_name_to_index = {name: i for i, name in enumerate(sim.body_names)}
    sim.contact_forces = torch.zeros((sim.num_envs, sim.num_bodies, 3))
    sim.contact_forces_history = torch.zeros((sim.num_envs, 2, sim.num_bodies, 3))
    sim._contact_slot_to_body_index = [2, 0]
    sim._contact_sensor = SimpleNamespace(
        data=SimpleNamespace(
            force=torch.tensor(
                [
                    [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                    [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]],
                ],
                dtype=torch.float32,
            )
        )
    )
    return sim


def test_contact_force_mapping_uses_consistent_index_space() -> None:
    sim = _build_simulator()
    sim._update_contact_forces_from_sensor()

    assert sim.find_rigid_body_indice("right_foot") == 2
    assert sim.find_rigid_body_indice("pelvis") == 0

    # Slot 0 maps to right_foot (index 2), slot 1 maps to pelvis (index 0).
    assert torch.allclose(sim.contact_forces[:, 2, :], torch.tensor([[1.0, 2.0, 3.0], [7.0, 8.0, 9.0]]))
    assert torch.allclose(sim.contact_forces[:, 0, :], torch.tensor([[4.0, 5.0, 6.0], [10.0, 11.0, 12.0]]))
    assert torch.all(torch.isfinite(sim.contact_forces))


def test_contact_force_history_clear_semantics() -> None:
    sim = _build_simulator()
    sim.contact_forces_history[:] = 1.0
    sim.clear_contact_forces_history(torch.tensor([1]))

    assert torch.all(sim.contact_forces_history[0] == 1.0)
    assert torch.allclose(sim.contact_forces_history[1], torch.zeros_like(sim.contact_forces_history[1]))

