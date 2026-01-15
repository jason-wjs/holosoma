#!/usr/bin/env python3
"""Visualize robot Q stand pose using viser."""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import viser  # type: ignore[import-not-found]
import yourdfpy  # type: ignore[import-not-found]
from viser.extras import ViserUrdf  # type: ignore[import-not-found]

# Q stand pose from robot.py (29 DOF for adam_sp)
Q_STAND_POSE_ADAM_SP = np.array(
    [
        -0.32,  # Left leg joints
        0.0,
        -0.18,
        0.66,
        -0.39,
        0.0,
        -0.32,  # Right leg joints
        0.0,
        0.18,
        0.66,
        -0.39,
        0.0,
        0.0,  # Waist joints
        0.0,
        0.0,
        0.0,
        0.1,  # Left arm joints
        0.0,
        -0.3,
        0.0,
        0.0,
        0.0,
        0.0,
        -0.1,  # Right arm joints
        0.0,
        -0.3,
        0.0,
        0.0,
        0.0,
    ]
)

# Q stand pose for g1 (29 DOF)
Q_STAND_POSE_G1 = np.array(
    [
        -0.312,  # Left leg joints
        0.0,
        0.0,
        0.669,
        -0.363,
        0.0,
        -0.312,  # Right leg joints
        0.0,
        0.0,
        0.669,
        -0.363,
        0.0,
        0.0,  # Waist joints
        0.0,
        0.0,
        0.2,  # Left arm joints
        0.2,
        0.0,
        0.6,
        0.0,
        0.0,
        0.0,
        0.2,  # Right arm joints
        -0.2,
        0.0,
        0.6,
        0.0,
        0.0,
        0.0,
    ]
)

# Robot base pose (position + quaternion wxyz)
ROOT_POS_ADAM_SP = np.array([0.0, 0.0, 0.85])  # Pelvis height
ROOT_POS_G1 = np.array([0.0, 0.0, 1.32])  # G1 height
ROOT_QUAT = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion (wxyz)


def visualize_robot(robot_type: str = "adam_sp"):
    """Visualize robot stand pose and print link positions.
    
    Args:
        robot_type: "adam_sp" or "g1"
    """
    script_dir = pathlib.Path(__file__).parent
    
    # Select robot configuration
    if robot_type == "adam_sp":
        urdf_path = script_dir / "models" / "adam_sp" / "adam_sp_29dof.urdf"
        if not urdf_path.exists():
            urdf_path = script_dir / "models" / "adam_sp" / "adam_sp_29dof_spherehand.urdf"
        q_stand_pose = Q_STAND_POSE_ADAM_SP
        root_pos = ROOT_POS_ADAM_SP
        link_names_to_check = ["toeTipLeft", "toeTipRight", "heelPadLeft", "heelPadRight", 
                               "midfootPadLeftInner", "midfootPadLeftOuter", 
                               "midfootPadRightInner", "midfootPadRightOuter"]
    elif robot_type == "g1":
        urdf_path = script_dir / "models" / "g1" / "g1_29dof.urdf"
        q_stand_pose = Q_STAND_POSE_G1
        root_pos = ROOT_POS_G1
        link_names_to_check = [f"left_ankle_roll_sphere_{i}_link" for i in range(1, 6)]
    else:
        print(f"Error: Unknown robot type: {robot_type}")
        sys.exit(1)
    
    if not urdf_path.exists():
        print(f"Error: URDF file not found: {urdf_path}")
        sys.exit(1)
    
    print(f"Loading URDF: {urdf_path}")
    print(f"Robot type: {robot_type}")
    
    # Setup viser server
    server = viser.ViserServer()
    
    # Add grid
    server.scene.add_grid(
        "/grid",
        width=2.0,
        height=2.0,
        position=(0.0, 0.0, 0.0),
    )
    
    # Create robot root frame
    robot_root = server.scene.add_frame("/robot", show_axes=True)
    
    # Set robot base pose
    robot_root.position = root_pos
    robot_root.wxyz = ROOT_QUAT
    
    # Load URDF
    robot_urdf = yourdfpy.URDF.load(
        str(urdf_path),
        load_meshes=True,
        build_scene_graph=True,
    )
    
    # Create ViserUrdf instance
    viser_robot = ViserUrdf(
        server,
        urdf_or_path=robot_urdf,
        root_node_name="/robot",
    )
    
    # Get actuated joint names and limits
    joint_limits = viser_robot.get_actuated_joint_limits()
    joint_names = list(joint_limits.keys())
    robot_dof = len(joint_names)
    
    print(f"Robot DOF: {robot_dof}")
    print(f"Joint names: {joint_names}")
    
    if robot_dof != len(q_stand_pose):
        print(f"Warning: Q_STAND_POSE has {len(q_stand_pose)} values, but robot has {robot_dof} DOF")
        print(f"Using first {robot_dof} values from Q_STAND_POSE")
        q_pose = q_stand_pose[:robot_dof]
    else:
        q_pose = q_stand_pose
    
    # Update robot configuration
    viser_robot.update_cfg(q_pose)
    
    print("\n" + "=" * 60)
    print("Visualization ready!")
    print("Open the URL printed above in your browser.")
    print("Press Ctrl+C to exit.")
    print("=" * 60)
    
    # Compute forward kinematics to get link positions
    # Create configuration dictionary for yourdfpy
    cfg_dict = {}
    for i, joint_name in enumerate(joint_names):
        if i < len(q_pose):
            cfg_dict[joint_name] = q_pose[i]
    
    # Get link transforms using yourdfpy scene graph
    # Update scene with current configuration
    robot_urdf.update_cfg(configuration=cfg_dict)
    
    # Print the 3D position of the links
    print(f"\nLink positions (in robot base frame) for {robot_type}:")
    
    for link_name in link_names_to_check:
        if link_name in robot_urdf.scene.graph.nodes:
            # Get the transform from scene graph
            transform, _ = robot_urdf.scene.graph.get(link_name)
            if transform is not None:
                position = transform[:3, 3]  # Extract translation from 4x4 matrix
                # Add root position offset
                world_position = position + root_pos
                print(f"{link_name:30s}: {position} (world: {world_position})")
            else:
                print(f"{link_name:30s}: Transform is None")
        else:
            print(f"{link_name:30s}: NOT FOUND in scene graph")
    
    # Keep running
    try:
        while True:
            import time
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nExiting...")


def main():
    """Main function - visualize robot stand pose."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize robot stand pose")
    parser.add_argument(
        "--robot",
        type=str,
        choices=["adam_sp", "g1"],
        default="g1",
        help="Robot type to visualize (default: g1)",
    )
    args = parser.parse_args()
    
    visualize_robot(args.robot)


if __name__ == "__main__":
    main()

