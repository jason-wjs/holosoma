from holosoma.config_values import randomization as randomization_values


def test_mjlab_randomization_preset_registered() -> None:
    assert "g1_29dof_mjlab" in randomization_values.DEFAULTS


def test_mjlab_randomization_excludes_unsupported_startup_terms() -> None:
    cfg = randomization_values.DEFAULTS["g1_29dof_mjlab"]
    setup_terms = set(cfg.setup_terms.keys())

    assert "mass_randomizer" not in setup_terms
    assert "randomize_friction_startup" not in setup_terms
    assert "randomize_base_com_startup" not in setup_terms

