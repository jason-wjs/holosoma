"""Default observation manager configurations."""

from holosoma.config_values.loco.adam_pro.observation import adam_pro_29dof_loco_single_wolinvel
from holosoma.config_values.loco.g1.observation import g1_29dof_loco_single_wolinvel
from holosoma.config_values.loco.t1.observation import t1_29dof_loco_single_wolinvel
from holosoma.config_values.wbt.g1.observation import g1_29dof_wbt_observation, g1_29dof_wbt_observation_w_object

none = None

def _get_adam_pro_29dof_wbt_observation():
    from holosoma.config_values.wbt.adam_pro.observation import adam_pro_29dof_wbt_observation
    return adam_pro_29dof_wbt_observation

DEFAULTS = {
    "none": none,
    "adam_pro_29dof_loco_single_wolinvel": adam_pro_29dof_loco_single_wolinvel,
    "t1_29dof_loco_single_wolinvel": t1_29dof_loco_single_wolinvel,
    "g1_29dof_loco_single_wolinvel": g1_29dof_loco_single_wolinvel,
    "g1_29dof_wbt": g1_29dof_wbt_observation,
    "g1_29dof_wbt_w_object": g1_29dof_wbt_observation_w_object,
    "adam_pro_29dof_wbt_observation": adam_pro_29dof_wbt_observation,
}
