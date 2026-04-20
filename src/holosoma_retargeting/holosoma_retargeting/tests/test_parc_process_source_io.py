from pathlib import Path

from holosoma_retargeting.parc_process.source_io import load_parc_sample


def test_load_parc_sample_reads_initial_aug_payload() -> None:
    sample = Path(
        "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
    )
    result = load_parc_sample(sample)
    assert result.motion_data.root_pos.shape[1] == 3
    assert result.motion_data.joint_rot.shape[2] == 4
    assert result.terrain_data.hf.ndim == 2
    assert "hf_mask_inds" in result.misc_data
