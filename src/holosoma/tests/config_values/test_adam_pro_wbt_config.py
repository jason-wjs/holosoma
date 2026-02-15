import importlib

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


def test_adam_pro_wbt_uses_29dof_robot_profile() -> None:
    cfg = DEFAULTS["adam_pro_29dof_wbt"]
    fast_sac_cfg = DEFAULTS["adam_pro_29dof_wbt_fast_sac"]

    assert cfg.robot.dof_obs_size == 29
    assert fast_sac_cfg.robot.dof_obs_size == 29
    assert "wristYaw_Left" in cfg.robot.dof_names
    assert "wristPitch_Left" in cfg.robot.dof_names
    assert "wristRoll_Left" in cfg.robot.dof_names


def test_adam_pro_wbt_reward_term_paths_are_importable() -> None:
    cfg = DEFAULTS["adam_pro_29dof_wbt"]
    for term_cfg in cfg.reward.terms.values():
        module_path, attr_name = term_cfg.func.split(":")
        module = importlib.import_module(module_path)
        assert hasattr(module, attr_name)


def test_adam_pro_wbt_bad_tracking_has_required_object_threshold_keys() -> None:
    cfg = DEFAULTS["adam_pro_29dof_wbt"]
    params = cfg.termination.terms["bad_tracking"].params
    assert "bad_object_pos_threshold" in params
    assert "bad_object_ori_threshold" in params
