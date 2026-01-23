#!/usr/bin/env python3
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import tyro
import viser  # type: ignore[import-not-found]  # pip install viser
import yourdfpy  # type: ignore[import-untyped]  # pip install yourdfpy
from viser.extras import ViserUrdf  # type: ignore[import-not-found]


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
@dataclass
class Config:
    # Path to the npz you saved from MuJoCo (with joint_pos, body_pos_w, body_lin_vel_w, etc.)
    npz_path: str

    # Robot URDF used for visualization
    robot_urdf: str

    # Robot type for joint name mapping (g1, t1, or adam_sp)
    robot_type: str = "g1"

    # Visualization settings
    grid_width: float = 2.0
    grid_height: float = 2.0
    show_meshes: bool = True
    loop: bool = True

    # Playback / visualization
    fps_override: float | None = None  # if None, use fps from npz
    vel_scale: float = 0.1  # length scale for velocity arrows
    vel_min_norm: float = 1e-2  # threshold below which we hide arrows


# ---------------------------------------------------------------------
# Joint name mappings
# ---------------------------------------------------------------------
def get_joint_names_for_robot(robot_type: str) -> list[str]:
    """Get the joint name list for a given robot type.
    
    Args:
        robot_type: Robot type ("g1", "t1", or "adam_sp").
    
    Returns:
        List of joint names in the expected order.
    """
    if robot_type == "g1" or robot_type == "t1":
        return [
            "left_hip_pitch_joint",
            "left_hip_roll_joint",
            "left_hip_yaw_joint",
            "left_knee_joint",
            "left_ankle_pitch_joint",
            "left_ankle_roll_joint",
            "right_hip_pitch_joint",
            "right_hip_roll_joint",
            "right_hip_yaw_joint",
            "right_knee_joint",
            "right_ankle_pitch_joint",
            "right_ankle_roll_joint",
            "waist_yaw_joint",
            "waist_roll_joint",
            "waist_pitch_joint",
            "left_shoulder_pitch_joint",
            "left_shoulder_roll_joint",
            "left_shoulder_yaw_joint",
            "left_elbow_joint",
            "left_wrist_roll_joint",
            "left_wrist_pitch_joint",
            "left_wrist_yaw_joint",
            "right_shoulder_pitch_joint",
            "right_shoulder_roll_joint",
            "right_shoulder_yaw_joint",
            "right_elbow_joint",
            "right_wrist_roll_joint",
            "right_wrist_pitch_joint",
            "right_wrist_yaw_joint",
        ]
    if robot_type == "adam_sp":
        return [
            "hipPitch_Left",
            "hipRoll_Left",
            "hipYaw_Left",
            "kneePitch_Left",
            "anklePitch_Left",
            "ankleRoll_Left",
            "hipPitch_Right",
            "hipRoll_Right",
            "hipYaw_Right",
            "kneePitch_Right",
            "anklePitch_Right",
            "ankleRoll_Right",
            "waistRoll",
            "waistPitch",
            "waistYaw",
            "shoulderPitch_Left",
            "shoulderRoll_Left",
            "shoulderYaw_Left",
            "elbow_Left",
            "wristYaw_Left",
            "wristPitch_Left",
            "wristRoll_Left",
            "shoulderPitch_Right",
            "shoulderRoll_Right",
            "shoulderYaw_Right",
            "elbow_Right",
            "wristYaw_Right",
            "wristPitch_Right",
            "wristRoll_Right",
        ]
    raise ValueError(f"Unknown robot type: {robot_type}")


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------
def load_npz_motion(npz_path: str):
    """
    Expected npz format:
        joint_pos      (T, 7 + ndof) OR (T, ndof)  # [root_xyz(3), root_quat(4), ndof] or just [ndof]
        joint_vel      (T, 6 + ndof) OR (T, ndof)  # [root_lin(3), root_ang(3), ndof] or just [ndof]
        body_pos_w     (T, nbody, 3)
        body_quat_w    (T, nbody, 4)
        body_lin_vel_w (T, nbody, 3)
        body_ang_vel_w (T, nbody, 3)
        joint_names    (ndof,)        # robot joints only, no free root (optional)
        body_names     (nbody,)       # (optional)
        fps            [fps]
        (optionally) object_* fields ignored here
    """
    data = np.load(npz_path, allow_pickle=True)

    joint_pos = data["joint_pos"]  # (T, 7 + ndof) or (T, ndof)
    joint_vel = data["joint_vel"]  # (T, 6 + ndof) or (T, ndof)
    body_pos_w = data["body_pos_w"]  # (T, nbody, 3)
    body_quat_w = data["body_quat_w"]  # (T, nbody, 4)
    body_lin_vel_w = data["body_lin_vel_w"]  # (T, nbody, 3)
    body_ang_vel_w = data["body_ang_vel_w"]  # (T, nbody, 3)

    joint_names = list(data["joint_names"]) if "joint_names" in data else None
    body_names = list(data["body_names"]) if "body_names" in data else None

    # fps saved as [fps] or scalar
    if "fps" in data:
        fps_arr = np.array(data["fps"]).reshape(-1)
        fps = float(fps_arr[0])
    else:
        fps = 30.0

    return {
        "joint_pos": joint_pos,
        "joint_vel": joint_vel,
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "body_ang_vel_w": body_ang_vel_w,
        "joint_names": joint_names,
        "body_names": body_names,
        "fps": fps,
    }


# ---------------------------------------------------------------------
# Main visualization logic
# ---------------------------------------------------------------------
def main(cfg: Config) -> None:
    data = load_npz_motion(cfg.npz_path)

    joint_pos = data["joint_pos"]  # (T, 7 + ndof) or (T, ndof)
    joint_names_npz = data["joint_names"]  # names for ndof robot joints (or None)
    body_pos_w = data["body_pos_w"]  # (T, nbody, 3)
    body_lin_vel_w = data["body_lin_vel_w"]  # (T, nbody, 3)
    body_names = data["body_names"]  # (nbody,) or None
    fps_npz = data["fps"]

    T, nq_total = joint_pos.shape
    _, nbody, _ = body_pos_w.shape

    # Check if joint_pos contains root (7D) or just joints (ndof)
    # BeyondMimic format has root included; other formats may not
    has_root_in_joint_pos = nq_total > 29  # heuristic: if > 29, likely has root (7 + 29 = 36 for g1/t1)
    
    if has_root_in_joint_pos:
        # Split joint_pos into root + joints.
        # Layout: [0:3] root pos, [3:7] root quat (wxyz), [7:] robot joints
        root_pos_seq = joint_pos[:, 0:3]  # (T, 3)
        root_quat_seq = joint_pos[:, 3:7]  # (T, 4)
        joint_angles_seq = joint_pos[:, 7:]  # (T, ndof)
        ndof = joint_angles_seq.shape[1]
    else:
        # joint_pos only contains robot joints (dof format)
        # We need to reconstruct root from body_pos_w[0] (base/pelvis)
        joint_angles_seq = joint_pos  # (T, ndof)
        ndof = joint_angles_seq.shape[1]
        # Use first body as root position approximation
        root_pos_seq = body_pos_w[:, 0, :]  # (T, 3)
        # For rotation, we'll use identity or extract from body_quat_w
        root_quat_seq = data["body_quat_w"][:, 0, :]  # (T, 4) - base body quat

    print(f"[viser_body_vel_player] Loaded npz: {cfg.npz_path}")
    print(f"  frames: {T}, total joint_pos dim: {nq_total}, ndof: {ndof}")
    print(f"  bodies: {nbody}, fps (npz): {fps_npz}")
    print(f"  has_root_in_joint_pos: {has_root_in_joint_pos}")
    if joint_names_npz:
        print(f"  joint names (npz): {joint_names_npz}")
    if body_names:
        print(f"  body names (npz):  {body_names}")

    fps = cfg.fps_override if cfg.fps_override is not None else fps_npz
    print(f"  using fps: {fps}")

    # -------------------- Setup viser -------------------------
    server = viser.ViserServer()
    server.scene.add_grid(
        "/grid",
        width=cfg.grid_width,
        height=cfg.grid_height,
        position=(0.0, 0.0, 0.0),
    )

    # Root frame for the robot (this will follow root_pos / root_quat)
    robot_root = server.scene.add_frame("/robot", show_axes=False)

    # Load URDF (via yourdfpy so meshes are available)
    robot_urdf_y = yourdfpy.URDF.load(
        cfg.robot_urdf,
        load_meshes=True,
        build_scene_graph=True,
    )
    vr = ViserUrdf(server, urdf_or_path=robot_urdf_y, root_node_name="/robot")

    # Actuated joints & mapping between URDF order and npz joint layout
    joint_limits = vr.get_actuated_joint_limits()  # dict: name -> (lower, upper)
    urdf_joint_order = list(joint_limits.keys())
    robot_dof = len(urdf_joint_order)

    print(f"  URDF actuated joints ({robot_dof}): {urdf_joint_order}")

    if robot_dof != ndof:
        print(
            f"[WARN] URDF actuated joint count ({robot_dof}) != ndof in npz joint_pos ({ndof}). "
            "We will map by joint name. If names don't match, this will error."
        )

    # Get joint_names: from npz if available, otherwise from robot_type
    if joint_names_npz is not None:
        joint_names = joint_names_npz
        print(f"  Using joint names from npz")
    else:
        joint_names = get_joint_names_for_robot(cfg.robot_type)
        print(f"  Using joint names from robot_type '{cfg.robot_type}'")

    if len(joint_names) != ndof:
        print(
            f"[WARN] joint_names length ({len(joint_names)}) != ndof ({ndof}). "
            "This may cause issues."
        )

    # joint_names from npz correspond to the *robot joints only*, in MuJoCo order,
    # which matches joint_pos columns [7: 7 + ndof] (or [0: ndof] for dof format).
    #
    # Build: URDF joint -> column index in joint_angles_seq
    name_to_npz_joint_idx = {name: i for i, name in enumerate(joint_names)}
    urdf_to_jointangles_idx_list: list[int] = []
    for jname in urdf_joint_order:
        if jname not in name_to_npz_joint_idx:
            raise KeyError(f"URDF joint '{jname}' not found in joint_names. joint_names: {joint_names}")
        idx_npz = name_to_npz_joint_idx[jname]  # index in [0..ndof-1] for joint_angles_seq
        urdf_to_jointangles_idx_list.append(idx_npz)
    urdf_to_jointangles_idx = np.array(urdf_to_jointangles_idx_list, dtype=int)

    # Initial URDF configuration & base pose
    root_pos0 = root_pos_seq[0]
    root_quat0 = root_quat_seq[0]

    robot_root.position = root_pos0
    robot_root.wxyz = root_quat0

    initial_cfg = joint_angles_seq[0, urdf_to_jointangles_idx]
    vr.update_cfg(initial_cfg)

    # -------------------- GUI controls ------------------------
    with server.gui.add_folder("Playback"):
        playing_cb = server.gui.add_checkbox("Playing", initial_value=True)
        t_slider = server.gui.add_slider(
            "Frame",
            min=0,
            max=T - 1,
            step=1,
            initial_value=0,
        )

    with server.gui.add_folder("Display"):
        show_meshes_cb = server.gui.add_checkbox("Show meshes", initial_value=cfg.show_meshes)
        vel_scale_slider = server.gui.add_slider(
            "Velocity scale",
            min=0.0,
            max=1.0,
            step=0.01,
            initial_value=cfg.vel_scale,
        )

    @show_meshes_cb.on_update
    def _on_meshes_update(_event) -> None:
        vr.show_visual = bool(show_meshes_cb.value)

    # -------------------- Body COM positions ------------------
    # Visualize body COM positions as a small point cloud
    init_body_points = body_pos_w[0]  # (nbody, 3)
    body_colors = np.zeros((nbody, 3), dtype=np.float32)
    body_colors[:] = np.array([0, 255, 0], dtype=np.float32)  # green

    body_points_handle = server.scene.add_point_cloud(
        "/body_com",
        points=init_body_points,
        colors=body_colors,
        point_size=0.015,
        point_shape="circle",
    )

    # -------------------- Velocity line segments --------------
    # We draw velocity as line segments from body_pos_w to body_pos_w + v * scale
    init_vel_points = np.zeros((nbody, 2, 3), dtype=np.float32)
    vel_colors = np.zeros((nbody, 2, 3), dtype=np.float32)
    vel_colors[..., :] = np.array([255, 0, 0], dtype=np.float32)  # red

    vel_lines = server.scene.add_line_segments(
        "/body_velocity_world",
        points=init_vel_points,
        colors=vel_colors,
        line_width=3.0,
    )

    # -------------------- Frame update ------------------------
    def update_frame(frame_idx: int) -> None:
        idx = int(np.clip(frame_idx, 0, T - 1))

        # 1) Update robot root pose
        root_pos = root_pos_seq[idx]  # (3,)
        root_quat = root_quat_seq[idx]  # (4,) wxyz

        robot_root.position = root_pos
        robot_root.wxyz = root_quat

        # 2) Update URDF joint configuration
        cfg_vec = joint_angles_seq[idx, urdf_to_jointangles_idx]  # (robot_dof,)
        vr.update_cfg(cfg_vec)

        # 3) Update body COM points
        body_points_handle.points = body_pos_w[idx]

        # 4) Update velocity line segments
        pos = body_pos_w[idx]  # (nbody, 3)
        vel = body_lin_vel_w[idx] * float(vel_scale_slider.value)  # (nbody, 3)

        # vel_raw = body_lin_vel_w[idx]  # (nbody, 3)
        # norms = np.linalg.norm(vel_raw, axis=-1, keepdims=True)  # (nbody, 1)
        # norms_xy = np.linalg.norm(vel_raw[:, :2], axis=-1, keepdims=True)  # (nbody, 1)
        # eps = 1e-8

        # # Unit directions; zero out near-zero velocities to avoid NaNs
        # dirs = np.where(norms > eps, vel_raw / norms, 0.0)

        # Now every non-zero velocity has the same length = vel_scale_slider.value
        # vel = dirs * float(vel_scale_slider.value)  # (nbody, 3)

        # Hide small velocities (optional)
        # mask = norms_xy < cfg.vel_min_norm
        # vel = np.where(mask, 0.0, vel)

        pts = np.stack([pos, pos + vel], axis=1)  # (nbody, 2, 3)
        vel_lines.points = pts

    @t_slider.on_update
    def _on_slider_update(_event) -> None:
        update_frame(t_slider.value)

    # Initialize frame 0
    update_frame(0)

    # -------------------- Playback loop -----------------------
    dt = 1.0 / fps if fps > 0 else 1.0 / 30.0
    last_time = time.time()

    print(
        f"[viser_body_vel_player] Ready. Open the URL above to view. "
        f"{'Looping' if cfg.loop else 'One-shot'} playback at {fps:.2f} FPS."
    )

    while True:
        now = time.time()
        if playing_cb.value and (now - last_time) >= dt:
            last_time = now
            next_idx = int(t_slider.value) + 1
            if next_idx >= T:
                if cfg.loop:
                    next_idx = 0
                else:
                    next_idx = T - 1
                    playing_cb.value = False
            t_slider.value = next_idx  # triggers update_frame via callback

        time.sleep(0.002)


if __name__ == "__main__":
    cfg = tyro.cli(Config)
    main(cfg)

"""
# For G1/T1 robot:
python viser_body_vel_player.py \
--npz_path ../converted_res/robot_only/sub3_largebox_003_mj.npz \
--robot_urdf ../models/g1/g1_29dof.urdf \
--robot_type g1

# For Adam-SP robot:
python viser_body_vel_player.py \
--npz_path ../converted_res/robot_only/sub3_largebox_003_mj.npz \
--robot_urdf ../models/adam_sp/adam_sp.urdf \
--robot_type adam_sp
"""
