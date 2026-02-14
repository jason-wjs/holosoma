"""Whole Body Tracking termination presets for Adam Pro robot."""

from holosoma.config_types.termination import TerminationManagerCfg, TermCfg

adam_pro_29dof_wbt_termination = TerminationManagerCfg(
    terms={
        "bad_ref_tracking": TermCfg(
            func="holosoma.managers.termination.terms.wbt:bad_ref_tracking",
            params={
                "ref_pos_error_threshold": 0.5,  # TODO: Tune for Adam Pro (meters)
                "ref_ori_error_threshold": 1.0,  # TODO: Tune for Adam Pro (radians)
                "velocity_error_threshold": 2.0,  # TODO: Tune for Adam Pro (m/s)
            },
        ),
        "bad_joint_pos_limits": TermCfg(
            func="holosoma.managers.termination.terms.common:bad_joint_pos_limits",
            params={
                "clip_limit_to_violation_ratio": 0.98,  # TODO: Adjust for Adam Pro
            },
        ),
        "bad_contact": TermCfg(
            func="holosoma.managers.termination.terms.common:bad_contact",
            params={
                "max_undesired_contact_force": 200.0,  # TODO: Tune for Adam Pro (Newtons)
                "max_contact_duration": 0.1,  # seconds
            },
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_termination"]