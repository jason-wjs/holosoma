"""Whole Body Tracking reward presets for Adam Pro robot."""

from holosoma.config_types.reward import RewardManagerCfg, RewardTermCfg

adam_pro_29dof_wbt_reward = RewardManagerCfg(
    terms={
        # === Global Reference Tracking ===
        "motion_global_ref_position": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_ref_position_error_exp",
            params={
                "sigma": 0.3,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        "motion_global_ref_orientation": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_ref_orientation_error_exp",
            params={
                "sigma": 0.4,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        # === Relative Body Tracking ===
        "motion_relative_body_position": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_relative_body_position_error_exp",
            params={
                "sigma": 0.3,  # TODO: Tune for Adam Pro dynamics
            },
            weight=2.0,
        ),
        "motion_relative_body_orientation": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_relative_body_orientation_error_exp",
            params={
                "sigma": 0.4,  # TODO: Tune for Adam Pro dynamics
            },
            weight=2.0,
        ),
        # === Body Velocities ===
        "motion_global_body_lin_vel": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_body_lin_vel",
            params={
                "sigma": 1.0,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        "motion_global_body_ang_vel": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_body_ang_vel",
            params={
                "sigma": 3.14,  # TODO: Tune for Adam Pro dynamics
            },
            weight=0.5,
        ),
        # === Regularization ===
        "penalty_action_rate": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:penalty_action_rate",
            weight=-0.1,  # PPO standard
        ),
        "limits_dof_pos": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:limits_dof_pos",
            params={
                "soft_dof_pos_limit": 0.9,  # TODO: Adjust for Adam Pro joint limits
            },
            weight=-100.0,
        ),
        "undesired_contacts": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:UndesiredContacts",
            params={
                "threshold": 1.0,
                "undesired_contacts_body_names": "^(?!toeLeft$)(?!toeRight$).+$",
            },
            weight=-0.5,
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_reward"]
