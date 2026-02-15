from pathlib import Path

from holosoma.config_values.robot import g1_29dof
from holosoma.simulator.mjlab.entity_adapter import build_entity_cfg, get_robot_xml_path, resolve_asset_root
from holosoma.utils.module_utils import get_holosoma_root


def test_resolve_asset_root_handles_holosoma_prefix() -> None:
    resolved = resolve_asset_root("@holosoma/data/robots")
    assert resolved.startswith(get_holosoma_root())
    assert resolved.endswith("data/robots")


def test_get_robot_xml_path_uses_asset_root_and_xml_file() -> None:
    xml_path = get_robot_xml_path(g1_29dof)
    assert Path(xml_path).name == Path(g1_29dof.asset.xml_file).name
    assert str(xml_path).endswith(g1_29dof.asset.xml_file)


def test_build_entity_cfg_maps_initial_state() -> None:
    cfg = build_entity_cfg(g1_29dof)
    assert hasattr(cfg, "init_state")

    assert list(cfg.init_state.pos) == g1_29dof.init_state.pos
    assert list(cfg.init_state.rot) == g1_29dof.init_state.rot
    assert list(cfg.init_state.lin_vel) == g1_29dof.init_state.lin_vel
    assert list(cfg.init_state.ang_vel) == g1_29dof.init_state.ang_vel

    sample_joint = g1_29dof.dof_names[0]
    assert cfg.init_state.joint_pos is not None
    assert cfg.init_state.joint_pos[sample_joint] == g1_29dof.init_state.default_joint_angles[sample_joint]
