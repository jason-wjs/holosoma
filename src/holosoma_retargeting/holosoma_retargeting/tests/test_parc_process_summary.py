from __future__ import annotations

from pathlib import Path

from holosoma_retargeting.examples.parc_process import ParcProcessResult, _result_to_dict
from holosoma_retargeting.parc_process.output_writer import PairedOutputResult
from holosoma_retargeting.parc_process.workspace import ParcWorkspace


def test_parc_process_summary_reports_workspace_and_terrain_assets() -> None:
    task_dir = Path("/tmp/parc_process_workspace/workspace/platform_001")
    workspace = ParcWorkspace(
        task_name="platform_001",
        task_dir=task_dir,
        joints_file=task_dir / "human_joints.npy",
        object_dir=task_dir,
        asset_xml_path=task_dir / "box_assets.xml",
        scene_xml_path=task_dir / "g1_29dof_w_multi_boxes.xml",
        urdf_path=task_dir / "multi_boxes.urdf",
        obj_path=task_dir / "multi_boxes.obj",
        terrain_hf_path=task_dir / "terrain_hf.npy",
        terrain_collision_path=task_dir / "terrain_collision.json",
        joint_names=("root",),
    )
    result = ParcProcessResult(
        sample=Path("/data/platform_001.pkl"),
        task_name="platform_001",
        workspace=workspace,
        retarget_npz=Path("/tmp/parc_process_workspace/retargeted/platform_001_original.npz"),
        paired_output=PairedOutputResult(
            motion_name="platform_001_g1",
            motion_file=Path("/tmp/parc_process_bootstrap/platform_001_g1.pkl"),
            manifest_file=Path("/tmp/parc_process_bootstrap/motions.yaml"),
        ),
    )

    payload = _result_to_dict(result)

    assert payload["workspace_assets"] == {
        "human_joints": str(task_dir / "human_joints.npy"),
        "multi_boxes_obj": str(task_dir / "multi_boxes.obj"),
        "box_assets_xml": str(task_dir / "box_assets.xml"),
        "scene_xml": str(task_dir / "g1_29dof_w_multi_boxes.xml"),
        "multi_boxes_urdf": str(task_dir / "multi_boxes.urdf"),
    }
    assert payload["terrain_collision_assets"] == {
        "terrain_hf": str(task_dir / "terrain_hf.npy"),
        "terrain_collision": str(task_dir / "terrain_collision.json"),
        "terrain_visual": str(task_dir / "multi_boxes.obj"),
    }
