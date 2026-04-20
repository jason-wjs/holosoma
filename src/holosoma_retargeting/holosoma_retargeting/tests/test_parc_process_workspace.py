from pathlib import Path
from types import SimpleNamespace

import numpy as np

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.examples.robot_retarget import load_motion_data, validate_config
from holosoma_retargeting.parc_process.source_io import load_parc_sample
from holosoma_retargeting.parc_process.workspace import build_parc_workspace


def _platform_sample() -> Path:
    return Path(
        "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
    )


def _source_xml() -> Path:
    return Path("/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml")


def test_build_parc_workspace_creates_retarget_inputs(tmp_path: Path) -> None:
    sample = load_parc_sample(_platform_sample())

    workspace = build_parc_workspace(
        sample=sample,
        source_xml=_source_xml(),
        output_dir=tmp_path,
        task_name="platform_001",
    )

    assert workspace.task_dir.exists()
    assert workspace.joints_file.exists()
    assert workspace.object_dir.exists()
    assert workspace.scene_xml_path.exists()
    assert workspace.scene_xml_path.name == "g1_29dof_w_multi_boxes.xml"

    human_joints = np.load(workspace.joints_file)
    assert human_joints.shape == (sample.motion_data.root_pos.shape[0], 15, 3)


def test_parc_workspace_is_accepted_by_climbing_loader(tmp_path: Path) -> None:
    sample = load_parc_sample(_platform_sample())
    build_parc_workspace(
        sample=sample,
        source_xml=_source_xml(),
        output_dir=tmp_path,
        task_name="platform_001",
    )

    cfg = RetargetingConfig(
        task_type="climbing",
        data_format="parc_humanoid",
        task_name="platform_001",
        data_path=tmp_path,
    )
    validate_config(cfg)

    motion_cfg = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")
    human_joints, object_poses, smpl_scale = load_motion_data(
        task_type="climbing",
        data_format="parc_humanoid",
        data_path=tmp_path,
        task_name="platform_001",
        constants=SimpleNamespace(ROBOT_HEIGHT=1.32),
        motion_data_config=motion_cfg,
    )

    assert human_joints.shape == (sample.motion_data.root_pos.shape[0], 15, 3)
    assert object_poses.shape == (sample.motion_data.root_pos.shape[0], 7)
    assert smpl_scale > 0.0
