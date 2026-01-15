#!/usr/bin/env python3
# viser_batch.py
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import tyro
import viser  # type: ignore[import-not-found]  # pip install viser
import yourdfpy  # type: ignore[import-untyped]  # pip install yourdfpy
from viser.extras import ViserUrdf  # type: ignore[import-not-found]

src_root = Path(__file__).resolve().parent.parent
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
from holosoma_retargeting.config_types.viser import ViserConfig  # noqa: E402
from holosoma_retargeting.src.viser_utils import create_motion_control_sliders  # noqa: E402


@dataclass
class ViserBatchConfig:
    """Configuration for batch viser player visualization."""

    qpos_dir: str = "rt_results"
    """Directory containing .npz files with qpos data."""

    robot_urdf: str = "models/g1/g1_29dof.urdf"
    """Path to robot URDF file."""

    object_urdf: str | None = None
    """Path to object URDF file (optional)."""

    fps: int = 30
    """Frames per second for playback."""

    assume_object_in_qpos: bool = True
    """Whether object pose is included in qpos array."""

    loop: bool = False
    """Whether to loop playback."""

    show_meshes: bool = True
    """Whether to show mesh visualizations."""

    grid_width: float = 8.0
    """Grid width for visualization."""

    grid_height: float = 8.0
    """Grid height for visualization."""

    visual_fps_multiplier: int = 2
    """Visual FPS multiplier for interpolation."""

    min_fps: int = 1
    """Minimum FPS setting."""

    max_fps: int = 240
    """Maximum FPS setting."""

    min_interp_mult: int = 1
    """Minimum interpolation multiplier."""

    max_interp_mult: int = 8
    """Maximum interpolation multiplier."""


def load_npz(npz_path: str):
    """Load qpos data from .npz file."""
    data = np.load(npz_path, allow_pickle=True)
    # expected: qpos [T, ?], and optional fps
    qpos = data["qpos"]
    fps = int(data["fps"]) if "fps" in data else 30
    return qpos, fps


def find_npz_files(directory: str) -> list[tuple[str, Path]]:
    """Find all .npz files in the specified directory (recursively)."""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    npz_files = []
    for npz_path in dir_path.rglob("*.npz"):
        # Get relative path from the directory for display
        rel_path = npz_path.relative_to(dir_path)
        npz_files.append((str(rel_path), npz_path))

    if not npz_files:
        raise ValueError(f"No .npz files found in directory: {directory}")

    # Sort by path for consistent ordering
    npz_files.sort(key=lambda x: x[0])
    return npz_files


def make_batch_player(config: ViserBatchConfig):
    """
    Create a batch player that can visualize multiple .npz files from a directory.

    The player allows switching between different motion files via a dropdown menu.
    """
    # Find all .npz files
    npz_files = find_npz_files(config.qpos_dir)
    print(f"Found {len(npz_files)} .npz files in {config.qpos_dir}")

    # Create server
    server = viser.ViserServer()

    # Root frames
    robot_root = server.scene.add_frame("/robot", show_axes=False)
    object_root = server.scene.add_frame("/object", show_axes=False)

    # Load URDFs
    robot_urdf_y = yourdfpy.URDF.load(config.robot_urdf, load_meshes=True, build_scene_graph=True)
    vr = ViserUrdf(server, urdf_or_path=robot_urdf_y, root_node_name="/robot")

    vo = None
    if config.object_urdf:
        object_urdf_y = yourdfpy.URDF.load(config.object_urdf, load_meshes=True, build_scene_graph=True)
        vo = ViserUrdf(server, urdf_or_path=object_urdf_y, root_node_name="/object")

    # Add grid
    server.scene.add_grid("/grid", width=config.grid_width, height=config.grid_height, position=(0.0, 0.0, 0.0))

    # Figure robot DOF
    joint_limits = vr.get_actuated_joint_limits()
    robot_dof = len(joint_limits)

    # Set initial mesh visibility
    vr.show_visual = config.show_meshes
    if vo is not None:
        vo.show_visual = config.show_meshes

    # ---------- Load all motion files ----------
    motion_data: Dict[str, tuple[np.ndarray, int]] = {}
    for rel_path, npz_path in npz_files:
        try:
            qpos, fps = load_npz(str(npz_path))
            motion_data[rel_path] = (qpos, fps)
            print(f"  Loaded: {rel_path} ({qpos.shape[0]} frames, fps={fps})")
        except Exception as e:
            print(f"  Warning: Failed to load {rel_path}: {e}")

    if not motion_data:
        raise ValueError("No valid .npz files could be loaded")

    # ---------- File selection GUI ----------
    file_names = list(motion_data.keys())
    current_file = {"name": file_names[0]}

    with server.gui.add_folder("File Selection"):
        file_dropdown = server.gui.add_dropdown(
            "Motion File",
            options=file_names,
            initial_value=file_names[0],
        )
        # Display initial file info
        initial_qpos, initial_fps = motion_data[file_names[0]]
        print(f"Current file: {file_names[0]} ({initial_qpos.shape[0]} frames, fps={initial_fps})")

    # ---------- Display controls ----------
    with server.gui.add_folder("Display"):
        show_meshes_cb = server.gui.add_checkbox("Show meshes", initial_value=config.show_meshes)

    @show_meshes_cb.on_update
    def _(_):
        vr.show_visual = bool(show_meshes_cb.value)
        if vo is not None:
            vo.show_visual = bool(show_meshes_cb.value)

    # ---------- Motion control sliders with mutable sequence ----------
    # Use a mutable container so we can update the motion sequence when switching files
    initial_qpos, initial_fps = motion_data[file_names[0]]
    actual_fps = initial_fps if initial_fps > 0 else config.fps
    
    # Mutable container for current motion data - this allows dynamic updates
    motion_container = {"qpos": initial_qpos, "fps": actual_fps}
    
    # Create a custom player that uses the mutable container
    has_object_input = (
        vo is not None
        and object_root is not None
        and config.assume_object_in_qpos
        and initial_qpos.shape[1] >= (7 + robot_dof + 7)
    )
    
    # GUI controls
    with server.gui.add_folder("Playback"):
        frame_slider = server.gui.add_slider(
            "Frame", min=0, max=max(0, initial_qpos.shape[0] - 1), step=1, initial_value=0
        )
        play_btn = server.gui.add_button("Play / Pause")
        fps_in = server.gui.add_number("FPS", initial_value=int(actual_fps), min=1, max=240, step=1)
    with server.gui.add_folder("Smoothing"):
        interp_mult_in = server.gui.add_number(
            "Visual FPS multiplier", initial_value=int(config.visual_fps_multiplier), min=1, max=8, step=1
        )
    
    # Helper functions (same as in viser_utils)
    def _quat_normalize(q: np.ndarray) -> np.ndarray:
        q = np.asarray(q, float)
        n = float(np.linalg.norm(q))
        return q if n == 0.0 else q / n

    def _quat_continuous(prev_q: np.ndarray | None, curr_q: np.ndarray) -> np.ndarray:
        q = _quat_normalize(curr_q)
        if prev_q is None:
            return q
        return -q if float(np.dot(prev_q, q)) < 0.0 else q

    def _slerp(q0: np.ndarray, q1: np.ndarray, u: float) -> np.ndarray:
        q0 = _quat_normalize(q0)
        q1 = _quat_normalize(q1)
        dot = float(np.dot(q0, q1))
        if dot < 0.0:
            q1 = -q1
            dot = -dot
        if dot > 0.9995:
            q = q0 + u * (q1 - q0)
            return _quat_normalize(q)
        theta = np.arccos(np.clip(dot, -1.0, 1.0))
        s = np.sin(theta)
        return (np.sin((1.0 - u) * theta) * q0 + np.sin(u * theta) * q1) / s

    def _interp_frame(qpos_arr: np.ndarray, i0: int, i1: int, u: float) -> np.ndarray:
        """SLERP for base & (optional) object quats; linear for positions and joints."""
        q0 = qpos_arr[i0]
        q1 = qpos_arr[i1]
        out = q0.copy()
        out[0:3] = (1.0 - u) * q0[0:3] + u * q1[0:3]  # pos (xyz)
        out[3:7] = _slerp(q0[3:7], q1[3:7], u)  # quat (wxyz)
        j0 = q0[7 : 7 + robot_dof]
        j1 = q1[7 : 7 + robot_dof]
        out[7 : 7 + robot_dof] = (1.0 - u) * j0 + u * j1
        if has_object_input:
            out[-7:-4] = (1.0 - u) * q0[-7:-4] + u * q1[-7:-4]  # obj pos (xyz)
            out[-4:] = _slerp(q0[-4:], q1[-4:], u)  # obj quat (wxyz)
        return out

    # State
    playing = {"flag": False}
    tick = {"next": time.perf_counter()}
    prev: dict[str, np.ndarray | None] = {"robot_q": None, "obj_q": None}
    nonlocal_f = {"f": 0.0}

    # Draw function
    def _apply_frame_from_q(q: np.ndarray) -> None:
        joints = q[7 : 7 + robot_dof]
        if joints.shape[0] != robot_dof:
            joints = (
                joints[:robot_dof] if joints.shape[0] > robot_dof else np.pad(joints, (0, robot_dof - joints.shape[0]))
            )
        vr.update_cfg(joints)
        robot_root.position = q[0:3]
        r_q = _quat_continuous(prev["robot_q"], q[3:7])
        prev["robot_q"] = r_q
        robot_root.wxyz = r_q
        if has_object_input and object_root is not None:
            object_root.position = q[-7:-4]
            o_q = _quat_continuous(prev["obj_q"], q[-4:])
            prev["obj_q"] = o_q
            object_root.wxyz = o_q

    def _apply_discrete_frame(i: int) -> None:
        qpos = motion_container["qpos"]
        n_frames = qpos.shape[0]
        i = int(np.clip(i, 0, n_frames - 1))
        _apply_frame_from_q(qpos[i])

    # Control callbacks
    @play_btn.on_click
    def _(_evt) -> None:
        playing["flag"] = not playing["flag"]
        tick["next"] = time.perf_counter()
        prev["robot_q"] = None
        prev["obj_q"] = None
        nonlocal_f["f"] = float(frame_slider.value)

    @fps_in.on_update
    def _(_evt) -> None:
        tick["next"] = time.perf_counter()

    @interp_mult_in.on_update
    def _(_evt) -> None:
        tick["next"] = time.perf_counter()

    @frame_slider.on_update
    def _(_evt) -> None:
        playing["flag"] = False
        tick["next"] = time.perf_counter()
        _apply_discrete_frame(int(frame_slider.value))
        prev["robot_q"] = None
        prev["obj_q"] = None
        nonlocal_f["f"] = float(frame_slider.value)

    # Player loop
    def _player_loop() -> None:
        while True:
            if playing["flag"]:
                qpos = motion_container["qpos"]
                n_frames = qpos.shape[0]
                if n_frames <= 1:
                    time.sleep(0.02)
                    continue
                    
                now = time.perf_counter()
                fps_val = max(1, int(fps_in.value))
                mult = max(1, int(interp_mult_in.value))
                dt = 1.0 / (fps_val * mult)

                if now >= tick["next"]:
                    f = nonlocal_f["f"] + 1.0 / mult
                    if config.loop:
                        f = f % max(1, n_frames)
                    else:
                        f = min(f, float(n_frames - 1))
                    nonlocal_f["f"] = f

                    k0 = int(np.floor(f))
                    k1 = (k0 + 1) % max(1, n_frames) if config.loop else min(k0 + 1, n_frames - 1)
                    u = float(f - k0)

                    q_interp = _interp_frame(qpos, k0, k1, u)
                    _apply_frame_from_q(q_interp)

                    if mult == 1:
                        frame_slider.value = k0

                    tick["next"] = now + dt
                else:
                    time.sleep(min(0.002, max(0.0, tick["next"] - now)))
            else:
                time.sleep(0.02)

    threading.Thread(target=_player_loop, daemon=True).start()
    _apply_discrete_frame(0)

    @file_dropdown.on_update
    def _(evt):
        """Handle file selection change - updates the motion sequence."""
        new_file = file_dropdown.value

        if new_file != current_file["name"]:
            current_file["name"] = new_file
            qpos, file_fps = motion_data[new_file]
            n_frames = qpos.shape[0]
            actual_fps = file_fps if file_fps > 0 else config.fps
            
            # Update the mutable container - this will be picked up by the player loop
            motion_container["qpos"] = qpos
            motion_container["fps"] = actual_fps
            
            # Update slider max and reset to frame 0
            frame_slider.max = max(0, n_frames - 1)
            frame_slider.value = 0
            fps_in.value = int(actual_fps)
            
            # Reset playback state
            playing["flag"] = False
            nonlocal_f["f"] = 0.0
            prev["robot_q"] = None
            prev["obj_q"] = None
            _apply_discrete_frame(0)
            
            print(f"Switched to: {new_file} ({n_frames} frames, fps={actual_fps})")

    # Print summary
    print(f"\n[viser_batch] Loaded {len(motion_data)} motion files")
    print(f"  robot_dof={robot_dof}")
    print(f"  object={'yes' if (config.object_urdf and config.assume_object_in_qpos) else 'no'}")
    print("Open the viewer URL printed above. Use the dropdown to switch between files.")
    print("Close the process (Ctrl+C) to exit.")

    return server


def main(cfg: ViserBatchConfig) -> None:
    """Main function for batch viser player."""
    make_batch_player(cfg)

    # Keep process alive
    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    cfg = tyro.cli(ViserBatchConfig)
    main(cfg)

