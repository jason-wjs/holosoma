from __future__ import annotations

from dataclasses import replace

import pytest

from holosoma.config_types.full_sim import FullSimConfig
from holosoma.config_values import experiment as experiment_values
from holosoma.simulator.mjlab.mjlab_simulator import MJLab
from holosoma.utils.safe_torch_import import torch


class _DummyTerrainManager:
    def get_state(self, _name: str):
        return None


@pytest.mark.mjlab
def test_mjlab_g1_flat_smoke() -> None:
    pytest.importorskip("mjlab")

    exp_cfg = experiment_values.DEFAULTS["g1_29dof_mjlab_flat"]
    training_cfg = replace(exp_cfg.training, num_envs=2, headless=True)
    full_cfg = FullSimConfig(
        simulator=exp_cfg.simulator.config,
        robot=exp_cfg.robot,
        training=training_cfg,
        logger=exp_cfg.logger,
        experiment_dir=None,
    )

    simulator = MJLab(tyro_config=full_cfg, terrain_manager=_DummyTerrainManager(), device="cpu")
    simulator.setup()
    simulator.setup_terrain()
    try:
        simulator.load_assets()
    except ImportError as exc:
        pytest.skip(f"MJLAB runtime unavailable in this environment: {exc}")

    base_init_state = torch.tensor(
        exp_cfg.robot.init_state.pos
        + exp_cfg.robot.init_state.rot
        + exp_cfg.robot.init_state.lin_vel
        + exp_cfg.robot.init_state.ang_vel,
        dtype=torch.float32,
        device="cpu",
    )
    env_origins = torch.zeros((training_cfg.num_envs, 3), dtype=torch.float32, device="cpu")
    simulator.create_envs(training_cfg.num_envs, env_origins, base_init_state)
    simulator.prepare_sim()

    zero_actions = torch.zeros((training_cfg.num_envs, simulator.num_dof), dtype=torch.float32, device="cpu")
    simulator.queue_dof_position_targets(zero_actions)
    for _ in range(3):
        simulator.simulate_at_each_physics_step()

    assert simulator.robot_root_states.shape == (training_cfg.num_envs, 13)
    assert simulator.dof_pos.shape == (training_cfg.num_envs, simulator.num_dof)
    assert simulator.contact_forces.shape[0] == training_cfg.num_envs
    assert torch.isfinite(simulator.robot_root_states).all()
    assert torch.isfinite(simulator.dof_pos).all()
