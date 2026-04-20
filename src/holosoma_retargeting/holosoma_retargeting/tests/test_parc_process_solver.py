from pathlib import Path

import numpy as np

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.retargeter import RetargeterConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.config_types.task import TaskConfig
from holosoma_retargeting.examples.robot_retarget import (
    build_retargeter_kwargs_from_config,
    create_task_constants,
    initialize_robot_pose,
    load_motion_data,
    setup_object_data,
)
from holosoma_retargeting.parc_process.source_io import load_parc_sample
from holosoma_retargeting.parc_process.workspace import build_parc_workspace
from holosoma_retargeting.src.interaction_mesh_retargeter import InteractionMeshRetargeter
from holosoma_retargeting.src.utils import (
    calculate_laplacian_coordinates,
    create_interaction_mesh,
    extract_foot_sticking_sequence_velocity,
    get_adjacency_list,
    preprocess_motion_data,
)


def _platform_sample() -> Path:
    return Path(
        "/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl"
    )


def _source_xml() -> Path:
    return Path("/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml")


def _build_frame0_problem(tmp_path: Path, *, activate_obj_non_penetration: bool):
    sample = load_parc_sample(_platform_sample())
    workspace = build_parc_workspace(
        sample=sample,
        source_xml=_source_xml(),
        output_dir=tmp_path,
        task_name="platform_001",
    )

    robot_cfg = RobotConfig(robot_type="g1")
    motion_cfg = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")
    task_cfg = TaskConfig(object_name="multi_boxes", object_dir=workspace.task_dir)
    constants = create_task_constants(robot_cfg, motion_cfg, task_cfg, "climbing")

    human_joints, object_poses, smpl_scale = load_motion_data(
        task_type="climbing",
        data_format="parc_humanoid",
        data_path=tmp_path,
        task_name="platform_001",
        constants=constants,
        motion_data_config=motion_cfg,
    )
    object_local_pts, object_local_pts_demo, object_urdf_path = setup_object_data(
        "climbing",
        constants,
        workspace.task_dir,
        smpl_scale,
        task_cfg,
        False,
    )
    retargeter = InteractionMeshRetargeter(
        **build_retargeter_kwargs_from_config(
            RetargeterConfig(
                activate_obj_non_penetration=activate_obj_non_penetration,
                activate_foot_sticking=False,
                activate_joint_limits=False,
                debug=False,
                visualize=False,
            ),
            constants,
            object_urdf_path,
            "climbing",
        )
    )

    human_joints, object_poses, _ = preprocess_motion_data(
        human_joints,
        retargeter,
        motion_cfg.toe_names,
        scale=smpl_scale,
        object_poses=object_poses,
    )
    q_init, _, object_poses_augmented, human_joints, _ = initialize_robot_pose(
        "climbing",
        "parc_humanoid",
        human_joints,
        object_poses,
        constants,
        retargeter,
        task_cfg,
        False,
        tmp_path / "retargeted",
        "platform_001",
    )
    foot_sticking = extract_foot_sticking_sequence_velocity(
        human_joints,
        retargeter.demo_joints,
        motion_cfg.toe_names,
    )[0]

    q_locked = np.zeros(retargeter.nq, dtype=np.float64)
    q_locked[retargeter.q_a_indices] = q_init
    q_locked[-7:] = object_poses_augmented[0]

    human_mapped_joints = human_joints[0, retargeter.smplh_mapped_joint_indices]
    source_vertices, source_tetrahedra = create_interaction_mesh(
        np.vstack([human_mapped_joints, object_local_pts_demo])
    )
    adj_list = get_adjacency_list(source_tetrahedra, len(source_vertices))
    target_laplacian = calculate_laplacian_coordinates(source_vertices, adj_list)

    return (
        retargeter,
        q_locked,
        target_laplacian,
        adj_list,
        object_local_pts,
        foot_sticking,
    )


def test_platform_frame0_respects_object_non_penetration_toggle(tmp_path: Path) -> None:
    (
        retargeter,
        q_locked,
        target_laplacian,
        adj_list,
        object_local_pts,
        foot_sticking,
    ) = _build_frame0_problem(tmp_path, activate_obj_non_penetration=False)

    _, phis = retargeter._update_jacobians_and_phis_from_q(q_locked)
    assert phis
    object_collision_pairs = [
        pair
        for pair in phis
        if retargeter.object_name in retargeter._geom_names[pair[0]]
        or retargeter.object_name in retargeter._geom_names[pair[1]]
    ]
    assert object_collision_pairs

    q_star, cost = retargeter.solve_single_iteration(
        q_locked=q_locked,
        q_a_n_last=q_locked[retargeter.q_a_indices],
        q_t_last=q_locked,
        target_laplacian=target_laplacian,
        adj_list=adj_list,
        obj_pts_local=object_local_pts,
        foot_sticking=foot_sticking,
        init_t=True,
        frame_idx=0,
    )

    assert q_star.shape == (retargeter.nq,)
    assert np.isfinite(cost)
