from holosoma.config_types.simulator import SimulatorInitConfig
from holosoma.config_values.experiment import DEFAULTS


def test_adam_pro_wbt_presets_registered() -> None:
    assert "adam_pro_29dof_wbt" in DEFAULTS
    assert "adam_pro_29dof_wbt_fast_sac" in DEFAULTS


def test_adam_pro_wbt_uses_simulator_init_config() -> None:
    cfg = DEFAULTS["adam_pro_29dof_wbt"]
    assert isinstance(cfg.simulator.config, SimulatorInitConfig)

    fast_sac_cfg = DEFAULTS["adam_pro_29dof_wbt_fast_sac"]
    assert isinstance(fast_sac_cfg.simulator.config, SimulatorInitConfig)
