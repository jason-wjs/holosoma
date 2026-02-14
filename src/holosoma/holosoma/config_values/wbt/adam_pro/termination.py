"""Whole Body Tracking termination presets for Adam Pro robot."""

from holosoma.config_types.termination import TerminationManagerCfg, TerminationTermCfg

adam_pro_29dof_wbt_termination = TerminationManagerCfg(
    terms={
        "timeout": TerminationTermCfg(
            func="holosoma.managers.termination.terms.common:timeout_exceeded",
            is_timeout=True,
        ),
        "motion_ends": TerminationTermCfg(
            func="holosoma.managers.termination.terms.wbt:motion_ends",
        ),
        "bad_tracking": TerminationTermCfg(
            func="holosoma.managers.termination.terms.wbt:BadTracking",
            params={
                "bad_ref_pos_threshold": 0.5,  # TODO: Tune for Adam Pro
                "bad_ref_ori_threshold": 0.8,  # TODO: Tune for Adam Pro
                "bad_motion_body_pos_threshold": 0.25,  # TODO: Tune for Adam Pro
                "body_names_to_track": [
                    "pelvis",
                    "torso_link",
                    "left_hip_pitch_link",
                    "left_knee_link",
                    "left_ankle_roll_link",
                    "right_hip_pitch_link",
                    "right_knee_link",
                    "right_ankle_roll_link",
                    "left_shoulder_pitch_link",
                    "left_elbow_link",
                    "left_wrist_yaw_link",
                    "right_shoulder_pitch_link",
                    "right_elbow_link",
                    "right_wrist_yaw_link",
                ],
                "bad_motion_body_pos_body_names": [
                    "left_ankle_roll_link",
                    "right_ankle_roll_link",
                    "left_wrist_yaw_link",
                    "right_wrist_yaw_link",
                ],
            },
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_termination"]
