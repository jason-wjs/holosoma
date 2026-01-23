"""Configuration types for data conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DataConversionConfig:
    """Configuration for data conversion.

    This follows the pattern from holosoma's config_types.
    Uses a flat structure with all conversion parameters.
    """

    input_file: str
    """Path to input motion file."""

    robot: Literal["g1", "t1", "adam_sp"] = "g1"
    """Robot model to use."""

    output_format: Literal["holosoma", "bm", "pbhc"] = "holosoma"
    """Output format: `holosoma` (legacy, includes names and optionally world) or `bm` (BeyondMimic/mjlab 7-field)."""

    robot_xml_path: str | None = None
    """Override MuJoCo XML path (takes precedence over `robot`/`object_name`)."""

    data_format: Literal["lafan", "smplh", "mocap", "bvh"] = "smplh"
    """Motion data format."""

    object_name: str | None = None
    """Override object name (default depends on robot and data type)."""

    input_fps: int = 30
    """FPS of the input motion."""

    output_fps: int = 50
    """FPS of the output motion."""

    output_joint_format: Literal["qpos", "dof"] = "qpos"
    """Export joint arrays as full MuJoCo qpos/qvel (`qpos`) or non-free joints only (`dof`)."""

    include_world_body: bool = True
    """Whether to include the implicit MuJoCo `world` body in `body_*` arrays and `body_names`."""

    line_range: tuple[int, int] | None = None
    """Line range (start, end) for loading data (both inclusive)."""

    has_dynamic_object: bool = False
    """Whether the motion has a dynamic object."""

    output_name: str | None = None
    """Name of the output motion npz file."""

    once: bool = False
    """Run the motion once and exit."""

    headless: bool = False
    """Do not open MuJoCo viewer; compute and save output only."""

    use_omniretarget_data: bool = False
    """Use OmniRetarget data format."""