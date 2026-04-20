from types import SimpleNamespace

import numpy as np

from holosoma_retargeting.config_types.data_type import PARC_HUMANOID_DEMO_JOINTS
from holosoma_retargeting.examples.robot_retarget import _compute_q_init_base
from holosoma_retargeting.src.utils import transform_from_human_to_world


def test_compute_q_init_base_supports_parc_humanoid_climbing() -> None:
    human_joints = np.zeros((1, len(PARC_HUMANOID_DEMO_JOINTS), 3), dtype=np.float64)
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("pelvis")] = np.array([0.0, 0.0, 0.95])
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("torso")] = np.array([0.0, 0.0, 1.18])
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("left_thigh")] = np.array([0.0, 0.10, 0.75])
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("right_thigh")] = np.array([0.0, -0.10, 0.75])

    q_init = _compute_q_init_base(
        task_type="climbing",
        data_format="parc_humanoid",
        human_joints=human_joints,
        object_poses=np.array([[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]], dtype=np.float64),
        constants=SimpleNamespace(ROBOT_DOF=29),
        retargeter=SimpleNamespace(demo_joints=PARC_HUMANOID_DEMO_JOINTS),
    )

    assert q_init.shape == (36,)
    np.testing.assert_allclose(
        q_init[:3],
        human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("torso")],
    )


def test_transform_from_human_to_world_handles_zero_object_offset() -> None:
    world_translation, quat = transform_from_human_to_world(
        human_initial_root=np.array([0.0, 0.0, 0.5], dtype=np.float64),
        object_initial_pose=np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64),
        local_translation=np.zeros(3, dtype=np.float64),
    )

    np.testing.assert_allclose(world_translation, np.zeros(3, dtype=np.float64))
    np.testing.assert_allclose(quat, np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64))
