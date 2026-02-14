"""Default command manager configurations."""

from holosoma.config_values.loco.adam_pro.command import adam_pro_29dof_command
from holosoma.config_values.loco.g1.command import g1_29dof_command
from holosoma.config_values.loco.t1.command import t1_29dof_command
from holosoma.config_values.wbt.adam_pro.command import adam_pro_29dof_wbt_command
from holosoma.config_values.wbt.g1.command import (
    g1_29dof_wbt_command,
    g1_29dof_wbt_command_w_object,
)

none = None

DEFAULTS = {
    "none": none,
    "adam_pro_29dof": adam_pro_29dof_command,
    "adam_pro_29dof_wbt": adam_pro_29dof_wbt_command,
    "t1_29dof": t1_29dof_command,
    "g1_29dof": g1_29dof_command,
    "g1_29dof_wbt": g1_29dof_wbt_command,
    "g1_29dof_wbt_w_object": g1_29dof_wbt_command_w_object,
}
