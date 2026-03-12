#!/usr/bin/env python3
"""批量可视化转换后的 NPZ：单窗口内通过下拉选择不同文件播放。"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tyro
import viser  # type: ignore[import-not-found]
import yourdfpy  # type: ignore[import-untyped]
from viser.extras import ViserUrdf  # type: ignore[import-not-found]

from viser_body_vel_player import load_npz_motion  # noqa: E402

ADAM_PRO_JOINT_ORDER = [
    "hipRoll_Left",
    "hipYaw_Left",
    "hipPitch_Left",
    "kneePitch_Left",
    "anklePitch_Left",
    "ankleRoll_Left",
    "hipRoll_Right",
    "hipYaw_Right",
    "hipPitch_Right",
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


def load_npz_motion_flexible(npz_path: str, urdf_joint_order: list[str] | None = None):
    """加载 NPZ，兼容含 joint_names 的格式与 BM 格式（无 names）。"""
    data = np.load(npz_path, allow_pickle=True)
    joint_pos = data["joint_pos"]
    body_pos_w = data["body_pos_w"]
    body_lin_vel_w = data["body_lin_vel_w"]
    body_quat_w = data.get("body_quat_w", np.zeros((*body_pos_w.shape[:2], 4)))
    joint_vel = data.get("joint_vel", np.zeros((joint_pos.shape[0], joint_pos.shape[1] - 1)))

    if "joint_names" in data:
        joint_names = list(data["joint_names"])
        body_names = list(data["body_names"]) if "body_names" in data else []
    else:
        nq = int(joint_pos.shape[1])
        urdf_dof = len(urdf_joint_order) if urdf_joint_order else 0
        if urdf_dof > 0 and nq in (urdf_dof, urdf_dof + 7):
            ndof = urdf_dof
        elif nq > 7:
            ndof = nq - 7
        else:
            ndof = nq
        joint_names = list(urdf_joint_order)[:ndof] if urdf_joint_order else [f"j{i}" for i in range(ndof)]
        body_names = [f"body_{i}" for i in range(body_pos_w.shape[1])]

    fps = 30.0
    if "fps" in data:
        fps_arr = np.array(data["fps"]).reshape(-1)
        if len(fps_arr) > 0:
            fps = float(fps_arr[0])

    return {
        "joint_pos": joint_pos,
        "joint_vel": joint_vel,
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "joint_names": joint_names,
        "body_names": body_names,
        "fps": fps,
    }


@dataclass
class Config:
    """批量 NPZ 可视化配置。"""

    npz_dir: str = "converted_bm/optitrack"
    """目录：包含待可视化的 .npz 文件"""

    robot_urdf: str = "models/adam_pro/adam_pro_29dof.urdf"
    """机器人 URDF 路径"""

    grid_width: float = 2.0
    grid_height: float = 2.0
    show_meshes: bool = True
    loop: bool = True
    fps_override: float | None = None
    vel_scale: float = 0.1


def main(cfg: Config) -> None:
    npz_dir = Path(cfg.npz_dir)
    if not npz_dir.is_dir():
        raise FileNotFoundError(f"NPZ 目录不存在: {npz_dir}")

    npz_files = sorted(npz_dir.glob("*.npz"))
    if not npz_files:
        raise FileNotFoundError(f"目录下无 .npz 文件: {npz_dir}")

    npz_paths = [str(p) for p in npz_files]
    labels = [p.name for p in npz_files]
    path_by_label = dict(zip(labels, npz_paths))

    print(f"[viser_body_vel_player_batch] 发现 {len(npz_paths)} 个 NPZ 文件")

    # 加载 URDF，创建 Viser 与 ViserUrdf（关节顺序必须从 vr 取，yourdfpy.URDF 无 get_actuated_joint_limits）
    robot_urdf_y = yourdfpy.URDF.load(cfg.robot_urdf, load_meshes=True, build_scene_graph=True)
    server = viser.ViserServer()
    server.scene.add_grid("/grid", width=cfg.grid_width, height=cfg.grid_height, position=(0.0, 0.0, 0.0))
    robot_root = server.scene.add_frame("/robot", show_axes=False)
    vr = ViserUrdf(server, urdf_or_path=robot_urdf_y, root_node_name="/robot")
    joint_limits = vr.get_actuated_joint_limits()
    urdf_joint_order = list(joint_limits.keys())
    robot_dof = len(urdf_joint_order)

    # 加载首个文件以初始化（兼容 BM 格式）
    first_path = npz_paths[0]
    try:
        data = load_npz_motion(first_path)
    except KeyError:
        data = load_npz_motion_flexible(first_path, urdf_joint_order)
    joint_pos = data["joint_pos"]
    joint_names = list(data["joint_names"])
    body_pos_w = data["body_pos_w"]
    body_quat_w = data["body_quat_w"]
    body_lin_vel_w = data["body_lin_vel_w"]
    fps_npz = data["fps"]
    fps = cfg.fps_override if cfg.fps_override is not None else fps_npz

    T, nq_total = joint_pos.shape
    _, nbody, _ = body_pos_w.shape
    ndof = 0
    has_root_in_joint_pos = False

    def split_root_and_dof(
        jp: np.ndarray, jnames: list[str], bp: np.ndarray, bq: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        nq = int(jp.shape[1])
        if nq == robot_dof + 7 or (len(jnames) > 0 and nq - 7 == len(jnames)):
            root_pos_seq = jp[:, 0:3]
            root_quat_seq = jp[:, 3:7]
            dof_seq = jp[:, 7:]
            return root_pos_seq, root_quat_seq, dof_seq, 7
        if nq == robot_dof or (len(jnames) > 0 and nq == len(jnames)):
            root_pos_seq = bp[:, 0, :]
            root_quat_seq = bq[:, 0, :] if bq.ndim == 3 and bq.shape[1] > 0 else np.tile(
                np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32), (jp.shape[0], 1)
            )
            dof_seq = jp
            return root_pos_seq, root_quat_seq, dof_seq, 0
        if nq > 7:
            root_pos_seq = jp[:, 0:3]
            root_quat_seq = jp[:, 3:7]
            dof_seq = jp[:, 7:]
            return root_pos_seq, root_quat_seq, dof_seq, 7
        raise ValueError(f"不支持的 joint_pos 维度: {nq}")

    root_pos_seq, root_quat_seq, dof_pos_seq, dof_offset = split_root_and_dof(
        joint_pos, joint_names, body_pos_w, body_quat_w
    )
    ndof = dof_pos_seq.shape[1]
    has_root_in_joint_pos = dof_offset == 7

    def resolve_joint_name_order(npz_joint_names: list[str], ndof_j: int) -> tuple[list[str], str]:
        if len(npz_joint_names) == ndof_j and set(urdf_joint_order).issubset(set(npz_joint_names)):
            return npz_joint_names, "npz joint_names"
        if "adam_pro" in cfg.robot_urdf and ndof_j == len(ADAM_PRO_JOINT_ORDER):
            if set(urdf_joint_order).issubset(set(ADAM_PRO_JOINT_ORDER)):
                return ADAM_PRO_JOINT_ORDER, "adam_pro default order"
        if ndof_j == len(urdf_joint_order):
            return list(urdf_joint_order), "urdf joint order"
        raise KeyError(
            "无法建立关节映射：npz joint_names 与 URDF 不一致，且无法使用 adam_pro/urdf 顺序兜底。"
        )

    # 建立 URDF joint -> dof 序列索引映射（严格匹配，避免静默错位）
    def build_urdf_to_jointpos_cols_impl(jnames: list[str], ndof_j: int) -> np.ndarray:
        effective_joint_names, source = resolve_joint_name_order(jnames, ndof_j)
        print(f"  joint mapping source: {source}")
        name_to_idx = {n: i for i, n in enumerate(effective_joint_names)}
        cols = []
        for jname in urdf_joint_order:
            if jname not in name_to_idx:
                raise KeyError(f"URDF joint '{jname}' 不在有效 joint 顺序中")
            cols.append(name_to_idx[jname])
        return np.array(cols, dtype=int)

    urdf_to_jointpos_cols = build_urdf_to_jointpos_cols_impl(joint_names, ndof)

    # 当前数据（切换文件时更新）
    state = {
        "joint_pos": joint_pos,
        "dof_pos": dof_pos_seq,
        "root_pos": root_pos_seq,
        "root_quat": root_quat_seq,
        "body_pos_w": body_pos_w,
        "body_quat_w": body_quat_w,
        "body_lin_vel_w": body_lin_vel_w,
        "T": T,
        "urdf_to_jointpos_cols": urdf_to_jointpos_cols,
    }

    robot_root.position = root_pos_seq[0]
    robot_root.wxyz = root_quat_seq[0]
    vr.update_cfg(dof_pos_seq[0, urdf_to_jointpos_cols])
    vr.show_visual = cfg.show_meshes

    body_points_handle = server.scene.add_point_cloud(
        "/body_com",
        points=body_pos_w[0],
        colors=np.full((nbody, 3), [0, 255, 0], dtype=np.float32),
        point_size=0.015,
        point_shape="circle",
    )
    vel_lines = server.scene.add_line_segments(
        "/body_velocity_world",
        points=np.zeros((nbody, 2, 3), dtype=np.float32),
        colors=np.full((nbody, 2, 3), [255, 0, 0], dtype=np.float32),
        line_width=3.0,
    )

    with server.gui.add_folder("文件"):
        file_dropdown = server.gui.add_dropdown("选择 NPZ", options=labels, initial_value=labels[0])

    with server.gui.add_folder("Playback"):
        playing_cb = server.gui.add_checkbox("Playing", initial_value=True)
        t_slider = server.gui.add_slider("Frame", min=0, max=T - 1, step=1, initial_value=0)

    with server.gui.add_folder("Display"):
        show_meshes_cb = server.gui.add_checkbox("Show meshes", initial_value=cfg.show_meshes)
        vel_scale_slider = server.gui.add_slider("Velocity scale", min=0.0, max=1.0, step=0.01, initial_value=cfg.vel_scale)

    @show_meshes_cb.on_update
    def _on_meshes(_) -> None:
        vr.show_visual = bool(show_meshes_cb.value)

    def load_file(path: str) -> None:
        try:
            d = load_npz_motion(path)
        except KeyError:
            d = load_npz_motion_flexible(path, urdf_joint_order)
        jp = d["joint_pos"]
        bp = d["body_pos_w"]
        bq = d["body_quat_w"]
        bv = d["body_lin_vel_w"]
        jnames = list(d["joint_names"])
        root_pos_j, root_quat_j, dof_pos_j, dof_offset_j = split_root_and_dof(jp, jnames, bp, bq)
        ndof_j = dof_pos_j.shape[1]
        nf = jp.shape[0]
        state["joint_pos"] = jp
        state["dof_pos"] = dof_pos_j
        state["root_pos"] = root_pos_j
        state["root_quat"] = root_quat_j
        state["body_pos_w"] = bp
        state["body_quat_w"] = bq
        state["body_lin_vel_w"] = bv
        state["T"] = nf
        state["urdf_to_jointpos_cols"] = build_urdf_to_jointpos_cols_impl(jnames, ndof_j)
        t_slider.min = 0
        t_slider.max = max(0, nf - 1)
        t_slider.value = 0
        fmt = "root+joint" if dof_offset_j == 7 else "joint-only(BM)"
        print(f"  已加载: {Path(path).name} ({nf} 帧), format={fmt}, ndof={ndof_j}")

    def update_frame(frame_idx: int) -> None:
        jp = state["joint_pos"]
        dof = state["dof_pos"]
        root_pos = state["root_pos"]
        root_quat = state["root_quat"]
        bp = state["body_pos_w"]
        bv = state["body_lin_vel_w"]
        cols = state["urdf_to_jointpos_cols"]
        idx = int(np.clip(frame_idx, 0, jp.shape[0] - 1))

        robot_root.position = root_pos[idx]
        robot_root.wxyz = root_quat[idx]
        vr.update_cfg(dof[idx, cols])
        body_points_handle.points = bp[idx]
        pos, vel = bp[idx], bv[idx] * float(vel_scale_slider.value)
        vel_lines.points = np.stack([pos, pos + vel], axis=1)

    @t_slider.on_update
    def _on_slider(_) -> None:
        update_frame(t_slider.value)

    @file_dropdown.on_update
    def _on_file_change(_) -> None:
        sel = file_dropdown.value
        path = path_by_label.get(sel)
        if path:
            load_file(path)
            update_frame(0)

    update_frame(0)

    dt = 1.0 / fps if fps > 0 else 1.0 / 30.0
    last_time = time.time()
    print(f"[viser_body_vel_player_batch] 就绪。通过下拉切换 NPZ，{fps:.1f} FPS 播放。")

    while True:
        now = time.time()
        if playing_cb.value and (now - last_time) >= dt:
            last_time = now
            next_idx = int(t_slider.value) + 1
            T_cur = state["T"]
            if next_idx >= T_cur:
                next_idx = 0 if cfg.loop else T_cur - 1
                if not cfg.loop:
                    playing_cb.value = False
            t_slider.value = next_idx
        time.sleep(0.002)


if __name__ == "__main__":
    cfg = tyro.cli(Config)
    main(cfg)
