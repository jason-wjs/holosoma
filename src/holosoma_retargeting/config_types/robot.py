"""Configuration types for robot retargeting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

import numpy as np


# Default values per robot type
class RobotDefaults(TypedDict):
    robot_dof: int
    robot_height: float
    object_name: str


_ROBOT_DEFAULTS: dict[str, RobotDefaults] = {
    "g1": {"robot_dof": 29, "robot_height": 1.32, "object_name": "ground"},
    "t1": {"robot_dof": 23, "robot_height": 1.2, "object_name": "ground"},
    "adam_sp": {"robot_dof": 29, "robot_height": 1.67, "object_name": "ground"},
}


@dataclass(frozen=True)
class RobotConfig:
    """Unified configuration for all robot constants (G1, T1, ADAM_SP) using tyro.

    Uses properties instead of __post_init__ - much simpler!

    Example usage:
        # From CLI:
        config = tyro.cli(RobotConfig)  # --robot-type g1 --robot-dof 30

        # With defaults:
        config = RobotConfig(robot_type="g1")

        # Access values:
        robot_dof = config.ROBOT_DOF
        robot_height = config.ROBOT_HEIGHT
    """

    # Robot type selector - determines which defaults to use
    robot_type: Literal["g1", "t1", "adam_sp"] = "g1"

    # Robot configuration (optional overrides)
    robot_dof: int | None = None
    robot_height: float | None = None
    robot_name: str | None = None
    robot_urdf_file: str | None = None

    # Joint definitions (optional overrides)
    foot_sticking_links: list[str] | None = None

    # Robot-specific optional fields
    q_a_standing: np.ndarray | None = None  # G1 only

    # Manual joint limits
    manual_lb: dict[str, float] | None = None
    manual_ub: dict[str, float] | None = None
    manual_cost: dict[str, float] | None = None

    # Nominal tracking indices
    nominal_tracking_indices: np.ndarray | None = None

    # Basic robot properties
    def _robot_dof(self) -> int:
        """Get robot DOF - use override if provided, else use robot_type default."""
        if self.robot_dof is not None:
            return self.robot_dof
        return _ROBOT_DEFAULTS[self.robot_type]["robot_dof"]

    ROBOT_DOF = property(
        _robot_dof,
        doc="Get robot DOF - use override if provided, else use robot_type default.",
    )

    def _robot_height(self) -> float:
        """Get robot height - use override if provided, else use robot_type default."""
        if self.robot_height is not None:
            return self.robot_height
        return _ROBOT_DEFAULTS[self.robot_type]["robot_height"]

    ROBOT_HEIGHT = property(
        _robot_height,
        doc="Get robot height - use override if provided, else use robot_type default.",
    )

    def _robot_name(self) -> str:
        """Get robot name - use override if provided, else compute from robot_type and DOF."""
        if self.robot_name is not None:
            return self.robot_name
        return f"{self.robot_type}_{self.ROBOT_DOF}dof"

    ROBOT_NAME = property(
        _robot_name,
        doc="Get robot name - use override if provided, else compute from robot_type and DOF.",
    )

    def _robot_urdf_file(self) -> str:
        """Get robot URDF file path.
        
        URDF file path convention:
        - Default: models/{robot_type}/{robot_type}_{dof}dof.urdf
        - Can be overridden via robot_urdf_file parameter
        - Ensure the URDF file exists and is accessible from the working directory
        """
        if self.robot_urdf_file is not None:
            return self.robot_urdf_file
        return f"models/{self.robot_type}/{self.robot_type}_{self.ROBOT_DOF}dof.urdf"

    ROBOT_URDF_FILE = property(_robot_urdf_file, doc="Get robot URDF file path.")

    def _foot_sticking_links(self) -> list[str]:
        """Get foot sticking links - use override if provided, else use robot_type default."""
        if self.foot_sticking_links is not None:
            return self.foot_sticking_links

        if self.robot_type == "g1":
            return [
                "left_ankle_roll_sphere_1_link",
                "right_ankle_roll_sphere_1_link",
                "left_ankle_roll_sphere_2_link",
                "right_ankle_roll_sphere_2_link",
                "left_ankle_roll_sphere_3_link",
                "right_ankle_roll_sphere_3_link",
                "left_ankle_roll_sphere_4_link",
                "right_ankle_roll_sphere_4_link",
            ]
        if self.robot_type == "t1":
            return [
                "left_foot_sphere_1_link",
                "right_foot_sphere_1_link",
                "left_foot_sphere_2_link",
                "right_foot_sphere_2_link",
                "left_foot_sphere_3_link",
                "right_foot_sphere_3_link",
                "left_foot_sphere_4_link",
                "right_foot_sphere_4_link",
                "left_foot_sphere_5_link",
                "right_foot_sphere_5_link",
            ]
        if self.robot_type == "adam_sp":
            return [
                "toeLeft",
                "toeRight",
                "toeTipLeft",
                "toeTipRight",
                "heelPadLeft",
                "heelPadRight",
                "midfootPadLeft",
                "midfootPadRight",
            ]
        raise ValueError(f"Invalid robot type: {self.robot_type}")

    FOOT_STICKING_LINKS = property(
        _foot_sticking_links,
        doc="Get foot sticking links - use override if provided, else use robot_type default.",
    )

    def _q_a_standing(self) -> np.ndarray | None:
        """Get standing pose (G1 only)."""
        if self.q_a_standing is not None:
            return self.q_a_standing
        if self.robot_type == "g1":
            return np.array(
                [
                    -0.312,
                    0.0,
                    0.0,
                    0.669,
                    -0.363,
                    0.0,
                    -0.312,
                    0.0,
                    0.0,
                    0.669,
                    -0.363,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.2,
                    0.2,
                    0.0,
                    0.6,
                    0.0,
                    0.0,
                    0.0,
                    0.2,
                    -0.2,
                    0.0,
                    0.6,
                    0.0,
                    0.0,
                    0.0,
                ]
            )
        if self.robot_type == "adam_sp":
            return np.array(
                [
                    -0.32,
                    0.0,
                    -0.18,
                    0.66,
                    -0.39,
                    0.0,
                    -0.32,
                    0.0,
                    0.18,
                    0.66,
                    -0.39,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.1,
                    0.0,
                    -0.3,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -0.1,
                    0.0,
                    -0.3,
                    0.0,
                    0.0,
                    0.0,
                ]
            )
        return None

    Q_A_STANDING = property(_q_a_standing, doc="Get standing pose (G1 only).")

    def _manual_lb(self) -> dict[str, float]:
        """Get manual lower bounds."""
        if self.manual_lb is not None:
            return self.manual_lb

        base: dict[str, float] = {"3": -1.0, "4": -1.0, "5": -1.0, "6": -1.0}  # quaternion bounds

        if self.robot_type == "g1":
            base.update(
                {
                    "20": -0.3,  # waist roll
                    "21": -0.1,  # waist pitch
                    "26": -0.1,  # right wrist
                    "27": -0.1,
                    "28": -0.05,
                    "33": -0.1,  # left wrist
                    "34": -0.1,
                    "35": -0.05,
                }
            )
        # TODO: Add manual lower bounds for your new robot if needed
        # Example:
        # elif self.robot_type == "new_robot":
        #     base.update({
        #         "XX": -value,  # joint index: limit value
        #     })

        return base

    MANUAL_LB = property(_manual_lb, doc="Get manual lower bounds.")

    def _manual_ub(self) -> dict[str, float]:
        """Get manual upper bounds."""
        if self.manual_ub is not None:
            return self.manual_ub

        base: dict[str, float] = {"3": 1.0, "4": 1.0, "5": 1.0, "6": 1.0}  # quaternion bounds

        if self.robot_type == "g1":
            base.update(
                {
                    "20": 0.3,  # waist roll
                    "25": 1.4,  # right elbow
                    "26": 0.2,  # right wrist
                    "27": 0.3,
                    "28": 0.05,
                    "32": 1.4,  # elbow
                    "33": 0.2,  # left wrist
                    "34": 0.3,
                    "35": 0.05,
                }
            )
        # TODO: Add manual upper bounds for your new robot if needed
        # Example:
        elif self.robot_type == "new_robot":
            base.update({
                "XX": 0.1,  # joint index: limit value
            })

        return base

    MANUAL_UB = property(_manual_ub, doc="Get manual upper bounds.")

    def _manual_cost(self) -> dict[str, float]:
        """Get manual cost weights."""
        if self.manual_cost is not None:
            return self.manual_cost

        if self.robot_type == "g1":
            return {"19": 0.2, "20": 0.2}  # waist roll , waist pitch
        if self.robot_type == "adam_sp":
            ## add manual cost for foot and toe
            return {
                "8": 1.0,  # hipRoll_Left
                "9": 0.5,  # hipYaw_Left
                # "11": 0.1,  # anklePitch_Left
                # "12": 0.1,  # ankleRoll_Left
                "14": 1.0,  # hipRoll_Right
                "15": 0.5,  # hipYaw_Right
                # "17": 0.1,  # anklePitch_Right
                # "18": 0.1,  # ankleRoll_Right
                "19": 0.5,  # waistRoll
                "20": 0.5,  # waistPitch
                "21": 0.5,  # waistYaw
            }
        return {}

    MANUAL_COST = property(_manual_cost, doc="Get manual cost weights.")

    def _nominal_tracking_indices(self) -> np.ndarray:
        """Get nominal tracking indices."""
        if self.nominal_tracking_indices is not None:
            return self.nominal_tracking_indices

        if self.robot_type == "g1":
            return np.arange(19)
        if self.robot_type == "t1":
            return np.concatenate([np.arange(7), np.arange(11, 23)])
        if self.robot_type == "adam_sp":
            return np.arange(19)  #
        raise ValueError(f"Invalid robot type: {self.robot_type}")

    NOMINAL_TRACKING_INDICES = property(
        _nominal_tracking_indices,
        doc="Get nominal tracking indices.",
    )
