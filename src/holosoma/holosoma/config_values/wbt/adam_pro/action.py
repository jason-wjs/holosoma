"""Whole Body Tracking action presets for Adam Pro robot."""

from holosoma.config_types.action import ActionManagerCfg, ActionTermCfg

adam_pro_29dof_joint_pos = ActionManagerCfg(
    terms={
        "joint_control": ActionTermCfg(
            func="holosoma.managers.action.terms.joint_control:JointPositionActionTerm",
            params={},
            scale=1.0,  # WBT uses 1.0 (locomotion uses 0.25)
            clip=None,
        ),
    }
)

__all__ = ["adam_pro_29dof_joint_pos"]