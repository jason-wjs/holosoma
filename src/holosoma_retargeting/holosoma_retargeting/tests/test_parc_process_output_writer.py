from pathlib import Path

import numpy as np
import yaml

from holosoma_retargeting.parc_process.output_writer import write_paired_output
from holosoma_retargeting.parc_process.source_io import load_parc_sample


def test_write_paired_output_emits_manifest_and_motion(tmp_path: Path) -> None:
    sample = load_parc_sample(
        Path(
            "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
        )
    )
    qpos = np.zeros((32, 36), dtype=np.float32)
    qpos[:, 2] = 0.78
    qpos[:, 3] = 1.0

    result = write_paired_output(
        qpos=qpos,
        source_sample=sample,
        output_root=tmp_path,
        motion_name="platform_001_g1",
        scale_factor=0.91,
        workspace_path=tmp_path / "workspace",
        terrain_collision_path=tmp_path / "workspace" / "terrain_collision.json",
        terrain_hf_path=tmp_path / "workspace" / "terrain_hf.npy",
        terrain_visual_path=tmp_path / "workspace" / "multi_boxes.obj",
        retarget_config={"robot": "g1", "task_type": "climbing"},
    )

    assert result.motion_file.exists()
    assert result.manifest_file.exists()

    motion_data = result.load_motion_file()
    assert motion_data.motion_data is not None
    assert motion_data.motion_data.root_pos.shape == (32, 3)
    assert motion_data.motion_data.root_rot.shape == (32, 4)
    assert motion_data.motion_data.joint_rot.shape == (32, 29, 4)
    assert motion_data.terrain_data is not None
    assert motion_data.terrain_data.hf.shape == sample.terrain_data.hf.shape
    assert motion_data.misc_data["parc_process:source_sample"] == str(sample.path)
    assert motion_data.misc_data["parc_process:scale_factor"] == 0.91
    assert motion_data.misc_data["parc_process:terrain_collision_file"].endswith("terrain_collision.json")
    assert motion_data.misc_data["parc_process:terrain_hf_file"].endswith("terrain_hf.npy")
    assert motion_data.misc_data["parc_process:terrain_visual_file"].endswith("multi_boxes.obj")

    manifest = yaml.safe_load(result.manifest_file.read_text())
    assert manifest["motions"] == [
        {
            "file": str(result.motion_file),
            "weight": 1.0,
            "name": "platform_001_g1",
        }
    ]
