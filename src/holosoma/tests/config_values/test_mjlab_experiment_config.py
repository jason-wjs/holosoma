from holosoma.config_values import experiment as experiment_values


def test_mjlab_flat_experiment_registered() -> None:
    assert "g1_29dof_mjlab_flat" in experiment_values.DEFAULTS


def test_mjlab_flat_experiment_uses_mjlab_safe_defaults() -> None:
    cfg = experiment_values.DEFAULTS["g1_29dof_mjlab_flat"]

    assert cfg.simulator.config.name == "mjlab"
    assert cfg.terrain.terrain_term.mesh_type.value == "plane"
    assert cfg.randomization.setup_terms.get("mass_randomizer") is None
    assert cfg.action.terms["joint_control"].func.endswith("JointTargetActionTermMJLab")

