"""MJLAB action term using simulator-owned target buffers."""

from __future__ import annotations

from typing import Any, Callable

import torch

from holosoma.managers.action.terms.joint_control import JointPositionActionTerm


class JointTargetActionTermMJLab(JointPositionActionTerm):
    """Joint control term that writes position/velocity/effort targets for MJLAB."""

    def apply_actions(self) -> None:
        """Compute diagnostics torques and queue MJLAB targets on the simulator."""
        self.torques[:] = self._compute_torques(self._actions_after_delay)
        actions_scaled = self._actions_after_delay * self.action_scales
        control_type = self.env.robot_config.control.control_type

        if control_type == "P":
            targets = actions_scaled + self.env.default_dof_pos
            self._queue_targets("queue_dof_position_targets", targets)
        elif control_type == "V":
            targets = actions_scaled
            self._queue_targets("queue_dof_velocity_targets", targets)
        elif control_type == "T":
            self._queue_targets("queue_dof_effort_targets", self.torques)
        else:
            raise ValueError(f"Unknown controller type: {control_type}")

        self._prev_dof_vel.copy_(self.env.simulator.dof_vel)

    def _queue_targets(self, method_name: str, targets: torch.Tensor) -> None:
        queue_fn: Callable[[torch.Tensor], Any] | None = getattr(self.env.simulator, method_name, None)
        if not callable(queue_fn):
            raise AttributeError(
                f"MJLAB action term requires simulator method '{method_name}' "
                f"for target-based control semantics."
            )
        queue_fn(targets)
