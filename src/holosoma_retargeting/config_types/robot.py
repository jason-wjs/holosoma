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
                # "toeLeft",
                # "toeRight",
                "toeTipLeft",
                "toeTipRight",
                "heelPadLeftInner",
                "heelPadLeftOuter",
                "heelPadRightInner",
                "heelPadRightOuter",
                "midfootPadLeftInner",
                "midfootPadLeftOuter",
                "midfootPadRightInner",
                "midfootPadRightOuter",
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
        elif self.robot_type == "adam_sp":
            # G1 waist roll: range -0.52 to 0.52, manual_lb -0.3 (57.7% of range)
            # G1 waist pitch: range -0.52 to 0.52, manual_lb -0.1 (19.2% of range)
            # adam_sp waistRoll: range -0.279 to 0.279, apply same percentage
            # adam_sp waistPitch: range -0.663 to 1.361, apply same percentage
            base.update({
                # "11": -0.45, # ankle pitch left
                # "17": -0.45, # ankle pitch right
                "7": -1.85, # hip roll left
                "13": -1.85, # hip roll right
                "12": -0.2, # ankle roll left
                "18": -0.2, # ankle roll right
                "19": -0.161,  # waist roll (57.7% of -0.279)
                "20": -0.127,  # waist pitch (19.2% of -0.663)
            })

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
        elif self.robot_type == "adam_sp":
            # G1 waist roll: range -0.52 to 0.52, manual_ub 0.3 (57.7% of range)
            # G1 waist pitch: range -0.52 to 0.52, manual_ub 0.52 (100% of range)
            # adam_sp waistRoll: range -0.279 to 0.279, apply same percentage
            # adam_sp waistPitch: range -0.663 to 1.361, apply same percentage
            base.update({
                "7": 2.0, # hip roll left
                "13": 2.0, # hip roll right
                "12": 0.2,
                "18": 0.2,
                "19": 0.161,   # waist roll (57.7% of 0.279)
                "20": 0.55,   # waist pitch (100% of 1.361, full range)
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
                "7": 0.1,  # hip Pitch left
                 "13": 0.1,  # hip Pitch right
                # "11": 0.5, # ankle pitch left
                # "12": 0.5, # ankle roll left
                # "17": 0.5, # ankle pitch right
                # "18": 0.5, # ankle roll right
                # "14": 0.1,  # hipRoll_Right
                # "15": 0.1,  # hipYaw_Right
                "19": 0.2,  # waistRoll
                "20": 0.2,  # waistPitch
                "21": 0.2,  # waistYaw
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
            return np.arange(19)  # leg(12) an waist(3) joints for ADAM_SP
        raise ValueError(f"Invalid robot type: {self.robot_type}")

    NOMINAL_TRACKING_INDICES = property(
        _nominal_tracking_indices,
        doc="Get nominal tracking indices.",
    )
