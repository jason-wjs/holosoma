from pathlib import Path

from holosoma_retargeting.parc_process.source_fk import build_source_joint_positions
from holosoma_retargeting.parc_process.source_io import load_parc_sample


def test_build_source_joint_positions_returns_world_joints() -> None:
    sample = load_parc_sample(
        Path(
            "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
        )
    )
    xml_path = Path(
        "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml"
    )
    joint_positions, joint_names = build_source_joint_positions(sample.motion_data, xml_path)
    assert joint_positions.shape[0] == sample.motion_data.root_pos.shape[0]
    assert joint_positions.shape[1] == len(joint_names) == 15
    assert joint_positions.shape[2] == 3
