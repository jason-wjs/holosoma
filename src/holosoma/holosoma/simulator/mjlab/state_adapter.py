"""State conversion helpers between holosoma and MJLAB conventions."""

from __future__ import annotations

from holosoma.utils.safe_torch_import import torch


def quat_xyzw_to_wxyz(quat_xyzw: torch.Tensor) -> torch.Tensor:
    """Convert quaternion order from xyzw to wxyz."""
    return quat_xyzw[..., [3, 0, 1, 2]]


def quat_wxyz_to_xyzw(quat_wxyz: torch.Tensor) -> torch.Tensor:
    """Convert quaternion order from wxyz to xyzw."""
    return quat_wxyz[..., [1, 2, 3, 0]]


def root_state_holosoma_to_mjlab(root_state_xyzw: torch.Tensor) -> torch.Tensor:
    """Convert root state [pos, quat(xyzw), lin_vel, ang_vel] to MJLAB quaternion order."""
    root_state_wxyz = root_state_xyzw.clone()
    root_state_wxyz[..., 3:7] = quat_xyzw_to_wxyz(root_state_xyzw[..., 3:7])
    return root_state_wxyz


def root_state_mjlab_to_holosoma(root_state_wxyz: torch.Tensor) -> torch.Tensor:
    """Convert root state [pos, quat(wxyz), lin_vel, ang_vel] to holosoma quaternion order."""
    root_state_xyzw = root_state_wxyz.clone()
    root_state_xyzw[..., 3:7] = quat_wxyz_to_xyzw(root_state_wxyz[..., 3:7])
    return root_state_xyzw


def pack_root_state(
    pos: torch.Tensor,
    quat_xyzw: torch.Tensor,
    lin_vel: torch.Tensor,
    ang_vel: torch.Tensor,
) -> torch.Tensor:
    """Pack root state components into `[N, 13]`."""
    return torch.cat((pos, quat_xyzw, lin_vel, ang_vel), dim=-1)


def unpack_root_state(root_state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Unpack `[N, 13]` root state into `(pos, quat_xyzw, lin_vel, ang_vel)`."""
    return (
        root_state[..., 0:3],
        root_state[..., 3:7],
        root_state[..., 7:10],
        root_state[..., 10:13],
    )
