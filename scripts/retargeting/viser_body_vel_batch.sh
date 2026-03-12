#!/usr/bin/env bash
# 批量可视化转换后的 NPZ：单窗口内通过下拉选择不同文件播放。
#
# 用法（仓库根目录）:
#   bash scripts/retargeting/viser_body_vel_batch.sh
#   NPZ_DIR=other_dir bash scripts/retargeting/viser_body_vel_batch.sh
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)
source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"

cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

NPZ_DIR="${NPZ_DIR:-converted_bm_g1/custom_optitrack/}"
ROBOT_URDF="${ROBOT_URDF:-models/g1/g1_29dof.urdf}"

python data_conversion/viser_body_vel_player_batch.py \
  --npz-dir "${NPZ_DIR}" \
  --robot-urdf "${ROBOT_URDF}" \
  --fps-override 50 \
  "$@"
