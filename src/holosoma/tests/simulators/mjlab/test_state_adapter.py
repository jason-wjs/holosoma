import torch

from holosoma.simulator.mjlab.state_adapter import (
    pack_root_state,
    quat_wxyz_to_xyzw,
    quat_xyzw_to_wxyz,
    root_state_holosoma_to_mjlab,
    root_state_mjlab_to_holosoma,
    unpack_root_state,
)


def test_quaternion_roundtrip_xyzw_wxyz() -> None:
    quat_xyzw = torch.tensor([[0.1, 0.2, 0.3, 0.9]], dtype=torch.float32)
    quat_wxyz = quat_xyzw_to_wxyz(quat_xyzw)
    quat_xyzw_back = quat_wxyz_to_xyzw(quat_wxyz)
    assert torch.allclose(quat_xyzw, quat_xyzw_back)


def test_root_state_pack_unpack_shape_and_values() -> None:
    pos = torch.randn(4, 3)
    quat_xyzw = torch.randn(4, 4)
    lin_vel = torch.randn(4, 3)
    ang_vel = torch.randn(4, 3)

    root = pack_root_state(pos, quat_xyzw, lin_vel, ang_vel)
    assert root.shape == (4, 13)

    pos_u, quat_u, lin_u, ang_u = unpack_root_state(root)
    assert torch.allclose(pos, pos_u)
    assert torch.allclose(quat_xyzw, quat_u)
    assert torch.allclose(lin_vel, lin_u)
    assert torch.allclose(ang_vel, ang_u)


def test_root_state_holosoma_mjlab_roundtrip() -> None:
    root_holosoma = torch.randn(3, 13)
    root_mjlab = root_state_holosoma_to_mjlab(root_holosoma)
    roundtrip = root_state_mjlab_to_holosoma(root_mjlab)
    assert torch.allclose(root_holosoma, roundtrip)
