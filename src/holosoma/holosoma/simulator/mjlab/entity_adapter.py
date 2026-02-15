"""Entity config adapter from holosoma robot config to MJLAB EntityCfg."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from holosoma.config_types.robot import RobotConfig
from holosoma.utils.module_utils import get_holosoma_root

try:
    from mjlab.entity.entity import EntityArticulationInfoCfg, EntityCfg
except ImportError:  # pragma: no cover - allows adapter tests without mjlab installation
    @dataclass
    class _InitialStateCfg:
        pos: tuple[float, float, float]
        rot: tuple[float, float, float, float]
        lin_vel: tuple[float, float, float]
        ang_vel: tuple[float, float, float]
        joint_pos: dict[str, float] | None
        joint_vel: dict[str, float]

    @dataclass
    class EntityArticulationInfoCfg:
        actuators: tuple[Any, ...] = tuple()

    @dataclass
    class EntityCfg:
        InitialStateCfg = _InitialStateCfg

        init_state: _InitialStateCfg
        spec_fn: Callable[[], Any]
        articulation: EntityArticulationInfoCfg | None = None


def resolve_asset_root(asset_root: str) -> str:
    """Resolve holosoma-prefixed asset roots to an absolute filesystem path."""
    if asset_root.startswith("@holosoma/"):
        return asset_root.replace("@holosoma", get_holosoma_root(), 1)
    return asset_root


def get_robot_xml_path(robot_config: RobotConfig) -> Path:
    """Resolve the robot MJCF path from robot asset config."""
    root = Path(resolve_asset_root(robot_config.asset.asset_root))
    return root / robot_config.asset.xml_file


def build_entity_cfg(
    robot_config: RobotConfig,
    *,
    actuators: tuple[Any, ...] | None = None,
    spec_fn: Callable[[], Any] | None = None,
) -> EntityCfg:
    """Build MJLAB EntityCfg from a holosoma RobotConfig."""
    xml_path = get_robot_xml_path(robot_config)

    if spec_fn is None:
        def spec_fn() -> Any:
            import mujoco

            return mujoco.MjSpec.from_file(str(xml_path))

    init_state = EntityCfg.InitialStateCfg(
        pos=tuple(robot_config.init_state.pos),
        rot=tuple(robot_config.init_state.rot),
        lin_vel=tuple(robot_config.init_state.lin_vel),
        ang_vel=tuple(robot_config.init_state.ang_vel),
        joint_pos=dict(robot_config.init_state.default_joint_angles),
        joint_vel={name: 0.0 for name in robot_config.dof_names},
    )

    articulation = None
    if actuators is not None:
        articulation = EntityArticulationInfoCfg(actuators=tuple(actuators))

    return EntityCfg(
        init_state=init_state,
        spec_fn=spec_fn,
        articulation=articulation,
    )
