"""Whole Body Tracking config presets for Adam Pro robot."""

from holosoma.config_types.experiment import ExperimentConfig
from holosoma.config_values.wbt.adam_pro.experiment import (
    adam_pro_29dof_wbt,
    adam_pro_29dof_wbt_fast_sac,
)
from holosoma.config_values.wbt.adam_pro.action import adam_pro_29dof_joint_pos
from holosoma.config_values.wbt.adam_pro.command import adam_pro_29dof_wbt_command
from holosoma.config_values.wbt.adam_pro.curriculum import adam_pro_29dof_wbt_curriculum
from holosoma.config_values.wbt.adam_pro.observation import adam_pro_29dof_wbt_observation
from holosoma.config_values.wbt.adam_pro.randomization import adam_pro_29dof_wbt_randomization
from holosoma.config_values.wbt.adam_pro.reward import adam_pro_29dof_wbt_reward
from holosoma.config_values.wbt.adam_pro.termination import adam_pro_29dof_wbt_termination

__all__ = [
    "adam_pro_29dof_wbt",
    "adam_pro_29dof_wbt_fast_sac",
    "adam_pro_29dof_joint_pos",
    "adam_pro_29dof_wbt_command",
    "adam_pro_29dof_wbt_curriculum",
    "adam_pro_29dof_wbt_observation",
    "adam_pro_29dof_wbt_randomization",
    "adam_pro_29dof_wbt_reward",
    "adam_pro_29dof_wbt_termination",
]