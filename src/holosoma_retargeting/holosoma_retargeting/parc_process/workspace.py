from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from holosoma_retargeting.parc_process.source_fk import build_source_joint_positions
from holosoma_retargeting.parc_process.source_io import ParcSample
from holosoma_retargeting.parc_process.terrain_scene import export_parc_scene


@dataclass(frozen=True)
class ParcWorkspace:
    task_name: str
    task_dir: Path
    joints_file: Path
    object_dir: Path
    asset_xml_path: Path
    scene_xml_path: Path
    urdf_path: Path
    obj_path: Path
    terrain_hf_path: Path
    terrain_collision_path: Path
    joint_names: tuple[str, ...]


def build_parc_workspace(
    *,
    sample: ParcSample,
    source_xml: str | Path,
    output_dir: str | Path,
    task_name: str,
    object_name: str = "multi_boxes",
    scale_factor: float = 1.0,
    scale_source: dict[str, Any] | None = None,
) -> ParcWorkspace:
    root_dir = Path(output_dir).expanduser().resolve()
    task_dir = root_dir / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    human_joints, joint_names = build_source_joint_positions(sample.motion_data, source_xml)
    joints_file = task_dir / "human_joints.npy"
    np.save(joints_file, human_joints)

    scene = export_parc_scene(
        sample.terrain_data,
        task_dir,
        object_name=object_name,
        scale_factor=scale_factor,
        scale_source=scale_source,
    )

    return ParcWorkspace(
        task_name=task_name,
        task_dir=task_dir,
        joints_file=joints_file,
        object_dir=task_dir,
        asset_xml_path=scene.asset_xml_path,
        scene_xml_path=scene.scene_xml_path,
        urdf_path=scene.urdf_path,
        obj_path=scene.obj_path,
        terrain_hf_path=scene.terrain_hf_path,
        terrain_collision_path=scene.terrain_collision_path,
        joint_names=joint_names,
    )
