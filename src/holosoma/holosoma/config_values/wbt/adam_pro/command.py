"""Whole Body Tracking command presets for Adam Pro robot."""

from dataclasses import replace

from holosoma.config_types.command import CommandManagerCfg, CommandTermCfg, MotionConfig, NoiseToInitialPoseConfig

init_pose_config = NoiseToInitialPoseConfig(
    overall_noise_scale=1.0,
    dof_pos=0.1,  # TODO: Tune for Adam Pro
    root_pos=[0.05, 0.05, 0.01],
    root_rot=[0.1, 0.1, 0.2],
    root_lin_vel=[0.1, 0.1, 0.05],
    root_ang_vel=[0.1, 0.1, 0.1],
    object_pos=[0.05, 0.05, 0.0],
)

motion_config = MotionConfig(
    motion_file="holosoma/data/motions/adam_pro_29dof/whole_body_tracking/dance1_subject1_mj_fps50.npz",
    body_names_to_track=[
        # Core bodies (from actual motion file)
        "pelvis",
        "torso_link",
        # Left leg (link names from motion file)
        "left_hip_pitch_link",
        "left_knee_link",
        "left_ankle_roll_link",
        # Right leg
        "right_hip_pitch_link",
        "right_knee_link",
        "right_ankle_roll_link",
        # Left arm
        "left_shoulder_pitch_link",
        "left_elbow_link",
        "left_wrist_yaw_link",
        # Right arm
        "right_shoulder_pitch_link",
        "right_elbow_link",
        "right_wrist_yaw_link",
    ],
    body_name_ref=["torso_link"],  # Reference body for relative pose computation
    use_adaptive_timesteps_sampler=True,  # Enable adaptive sampling
    noise_to_initial_pose=init_pose_config,
)

adam_pro_29dof_wbt_command = CommandManagerCfg(
    params={},
    setup_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
            params={
                "motion_config": motion_config,
            },
        ),
    },
    reset_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        ),
    },
    step_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_command"]