#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)
source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

ROBOT_URDF="${ROBOT_URDF:-models/g1/g1_29dof_spherehand.urdf}"

## platform_001
python viser_player.py \
  --robot_urdf "${ROBOT_URDF}" \
  --object_urdf /tmp/parc_process_workspace/workspace/platform_001/multi_boxes_scaled_0.81_0.81_0.81.urdf \
  --qpos_npz /tmp/parc_process_workspace/retargeted/platform_001_original.npz \
  --no-assume-object-in-qpos \
  "$@"

## mid_blocks_004_dm
# python viser_player.py \
#   --robot_urdf "${ROBOT_URDF}" \
#   --object_urdf /tmp/parc_process_workspace/workspace/mid_blocks_004_dm/multi_boxes_scaled_0.74_0.74_0.74.urdf \
#   --qpos_npz /tmp/parc_process_workspace/retargeted/mid_blocks_004_dm_original.npz \
#   --no-assume-object-in-qpos \
#   "$@"

## beyond_platform_002
# python viser_player.py \
#   --robot_urdf "${ROBOT_URDF}" \
#   --object_urdf /tmp/parc_process_workspace_more/workspace/beyond_platform_002/multi_boxes_scaled_0.74_0.74_0.74.urdf \
#   --qpos_npz /tmp/parc_process_workspace_more/retargeted/beyond_platform_002_original.npz \
#   --no-assume-object-in-qpos \
#   "$@"
