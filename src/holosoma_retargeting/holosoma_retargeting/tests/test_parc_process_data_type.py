from holosoma_retargeting.config_types.data_type import MotionDataConfig


def test_parc_humanoid_format_is_registered_for_g1() -> None:
    cfg = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")

    assert "pelvis" in cfg.resolved_demo_joints
    assert cfg.resolved_joints_mapping["left_foot"]
    assert cfg.toe_names == ["left_foot", "right_foot"]
