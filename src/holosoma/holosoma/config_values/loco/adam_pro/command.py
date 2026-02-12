"""Locomotion command presets for the Adam Pro robot."""

from holosoma.config_types.command import CommandManagerCfg, CommandTermCfg

adam_pro_29dof_command = CommandManagerCfg(
    params={
        "locomotion_command_resampling_time": 8.0,
    },
    setup_terms={
        "locomotion_gait": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionGait",
            params={
                "gait_period": 1.0,
                "gait_period_randomization_width": 0.15,
            },
        ),
        "locomotion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.locomotion:LocomotionCommand",
            params={
                "command_ranges": {
                    "lin_vel_x": [-0.8, 1.2],
                    "lin_vel_y": [-0.6, 0.6],
                    "ang_vel_yaw": [-0.8, 0.8],
                    "heading": [-3.14, 3.14],
                },
                "stand_prob": 0.25,
            },
        ),
    },
    reset_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
    step_terms={
        "locomotion_gait": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionGait"),
        "locomotion_command": CommandTermCfg(func="holosoma.managers.command.terms.locomotion:LocomotionCommand"),
    },
)

__all__ = ["adam_pro_29dof_command"]
