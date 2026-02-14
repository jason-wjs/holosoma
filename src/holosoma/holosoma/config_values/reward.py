"""Default reward manager configurations."""

from holosoma.config_values.loco.adam_pro.reward import adam_pro_29dof_loco, adam_pro_29dof_loco_fast_sac
from holosoma.config_values.loco.g1.reward import g1_29dof_loco, g1_29dof_loco_fast_sac
from holosoma.config_values.loco.t1.reward import t1_29dof_loco, t1_29dof_loco_fast_sac
from holosoma.config_values.wbt.adam_pro.reward import adam_pro_29dof_wbt_reward
from holosoma.config_values.wbt.g1.reward import (
    g1_29dof_wbt_fast_sac_reward,
    g1_29dof_wbt_reward,
    g1_29dof_wbt_reward_w_object,
)

none = None

DEFAULTS = {
    "none": none,
    "adam_pro_29dof_loco": adam_pro_29dof_loco,
    "adam_pro_29dof_loco_fast_sac": adam_pro_29dof_loco_fast_sac,
    "t1_29dof_loco": t1_29dof_loco,
    "t1_29dof_loco_fast_sac": t1_29dof_loco_fast_sac,
    "g1_29dof_loco": g1_29dof_loco,
    "g1_29dof_loco_fast_sac": g1_29dof_loco_fast_sac,
    "adam_pro_29dof_wbt": adam_pro_29dof_wbt_reward,
    "g1_29dof_wbt": g1_29dof_wbt_reward,
    "g1_29dof_wbt_w_object": g1_29dof_wbt_reward_w_object,
    "g1_29dof_wbt_fast_sac": g1_29dof_wbt_fast_sac_reward,
}
