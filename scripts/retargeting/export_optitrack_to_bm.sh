#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"
ROBOT="${ROBOT:-g1}"
python data_conversion/convert_data_format_mj.py \
  --input-file "demo_results/g1/robot_only/bvh_from_1031/BOXING1_Skeleton 004_z_up_x_forward_gym.npz" \
  --data-format bvh \
  --output-format spider \
  --output-name "converted_spider_robot/g1/optitrack_original/BOXING1_Skeleton.npz" \
  --robot "${ROBOT}" \
  --object-name ground \
  --once \
  --output-fps 50 \
  --input-fps 30 \
  "$@"
