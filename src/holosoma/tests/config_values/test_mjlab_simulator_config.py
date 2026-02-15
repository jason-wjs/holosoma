from holosoma.config_values import simulator as simulator_values
from holosoma.utils.simulator_config import SimulatorType


def test_simulator_type_includes_mjlab() -> None:
    assert hasattr(SimulatorType, "MJLAB")
    assert SimulatorType.MJLAB.value == "mjlab"


def test_simulator_defaults_include_mjlab() -> None:
    assert "mjlab" in simulator_values.DEFAULTS


def test_mjlab_target_and_name_are_consistent() -> None:
    cfg = simulator_values.DEFAULTS["mjlab"]
    assert cfg.config.name == "mjlab"
    assert cfg._target_.split(".")[-1].lower() == cfg.config.name
