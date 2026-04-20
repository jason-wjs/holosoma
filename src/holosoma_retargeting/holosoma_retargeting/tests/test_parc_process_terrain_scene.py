from pathlib import Path

import mujoco

from holosoma_retargeting.parc_process.source_io import load_parc_sample
from holosoma_retargeting.parc_process.terrain_scene import export_parc_scene


def test_export_parc_scene_writes_obj_and_xml(tmp_path: Path) -> None:
    sample = load_parc_sample(
        Path(
            "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
        )
    )
    scene = export_parc_scene(sample.terrain_data, tmp_path, object_name="multi_boxes")
    assert scene.obj_path.exists()
    assert scene.scene_xml_path.exists()
    assert scene.asset_xml_path.exists()
    model = mujoco.MjModel.from_xml_path(str(scene.scene_xml_path))
    assert model.nbody > 0
