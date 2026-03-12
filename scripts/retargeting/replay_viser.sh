#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

python viser_player.py \
  --qpos-npz "demo_results/g1/robot_only/bvh_from_1031/BOXING1_Skeleton 004_z_up_x_forward_gym.npz" \
  --robot-urdf models/g1/g1_29dof.urdf \
  --fps 30 \
  --no-assume-object-in-qpos \
  --no-loop \
  --show-meshes \
  --grid-width 8.0 \
  --grid-height 8.0 \
  --visual-fps-multiplier 2 \
  "$@"

