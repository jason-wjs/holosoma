"""Locomotion action presets for the G1 robot."""

from holosoma.config_types.action import ActionManagerCfg, ActionTermCfg

g1_29dof_joint_pos = ActionManagerCfg(
    terms={
        "joint_control": ActionTermCfg(
            func="holosoma.managers.action.terms.joint_control:JointPositionActionTerm",
            params={},
            scale=1.0,
            clip=None,
        ),
    }
)

g1_29dof_joint_target_mjlab = ActionManagerCfg(
    terms={
        "joint_control": ActionTermCfg(
            func="holosoma.managers.action.terms.joint_control_mjlab:JointTargetActionTermMJLab",
            params={},
            scale=1.0,
            clip=None,
        ),
    }
)

__all__ = ["g1_29dof_joint_pos", "g1_29dof_joint_target_mjlab"]
