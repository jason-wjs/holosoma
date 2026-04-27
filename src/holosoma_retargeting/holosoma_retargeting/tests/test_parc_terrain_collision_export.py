from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from holosoma_retargeting.parc_process.source_io import ParcTerrainData
from holosoma_retargeting.parc_process.terrain_scene import export_parc_scene


def test_export_parc_scene_writes_heightfield_collision_manifest(tmp_path: Path) -> None:
    terrain = ParcTerrainData(
        hf=np.array([[0.0, 0.2], [0.4, 0.6]], dtype=np.float32),
        hf_maxmin=np.array([0.6, 0.0], dtype=np.float32),
        min_point=np.array([-1.0, -2.0], dtype=np.float32),
        dx=0.4,
    )

    assets = export_parc_scene(
        terrain,
        tmp_path,
        object_name="multi_boxes",
        scale_factor=0.5,
        scale_source={
            "robot_type": "test_bot",
            "robot_height": 1.0,
            "data_format": "parc_humanoid",
            "default_human_height": 2.0,
            "rule": "test scale",
        },
    )

    assert assets.terrain_hf_path.is_file()
    assert assets.terrain_collision_path.is_file()
    np.testing.assert_allclose(np.load(assets.terrain_hf_path), terrain.hf)

    manifest = json.loads(assets.terrain_collision_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["terrain_name"] == "multi_boxes"
    assert manifest["collision"]["type"] == "heightfield"
    assert manifest["collision"]["hf_file"] == "terrain_hf.npy"
    assert manifest["collision"]["min_point"] == [-1.0, -2.0]
    assert manifest["collision"]["dx"] == 0.4
    assert manifest["collision"]["base_z"] == -0.2
    assert manifest["collision"]["xy_scale"] == 0.5
    assert manifest["collision"]["height_scale"] == 0.5
    assert manifest["source"]["scale_source"]["default_human_height"] == 2.0
    assert manifest["visual"]["file"] == "multi_boxes.obj"
    assert manifest["visual"]["role"] == "visual_only"
