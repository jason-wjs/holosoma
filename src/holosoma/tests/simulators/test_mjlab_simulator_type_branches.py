from __future__ import annotations

import importlib
from types import SimpleNamespace

from holosoma.config_values.simulator import mjlab as mjlab_simulator_cfg
from holosoma.simulator.shared.virtual_gantry import VirtualGantry
from holosoma.utils import eval_utils, sim_utils
from holosoma.utils.simulator_config import SimulatorType, set_simulator_type_enum


def test_draw_module_supports_mjlab_branch_without_exception() -> None:
    set_simulator_type_enum(SimulatorType.MJLAB)
    draw = importlib.import_module("holosoma.utils.draw")
    draw = importlib.reload(draw)

    # Should be callable no-op stubs for MJLAB.
    draw.clear_lines(None)
    draw.draw_line(None, [0, 0, 0], [1, 1, 1])


def test_sim_utils_setup_imports_handles_mjlab() -> None:
    set_simulator_type_enum(SimulatorType.MJLAB)
    cfg = SimpleNamespace(simulator=mjlab_simulator_cfg)
    sim_utils.setup_simulator_imports(cfg)


def test_eval_utils_init_sim_imports_no_crash_for_mjlab() -> None:
    set_simulator_type_enum(SimulatorType.MJLAB)
    cfg = SimpleNamespace(simulator=mjlab_simulator_cfg)
    app = eval_utils.init_sim_imports(cfg)
    assert app is None


def test_virtual_gantry_mjlab_no_crash_path() -> None:
    set_simulator_type_enum(SimulatorType.MJLAB)
    fake_sim = SimpleNamespace(
        num_envs=1,
        robot_root_states=SimpleNamespace(),
        device="cpu",
    )

    gantry = VirtualGantry(sim=fake_sim, body_link_id=0, enable=False)
    assert gantry.enabled is False

