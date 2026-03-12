#!/usr/bin/env bash
# 批量将 OptiTrack 重定向结果目录下的 NPZ 转为 BM 格式。
# 输出文件名只取原文件名「第一个空格前」的部分，如：
#   BOXING4_Skeleton 004_z_up_x_forward_gym_original.npz -> BOXING4_Skeleton.npz
#
# 用法（仓库根目录）:
#   bash scripts/retargeting/export_optitrack_to_bm_batch.sh
#   INPUT_DIR=other_input OUTPUT_DIR=other_bm bash scripts/retargeting/export_optitrack_to_bm_batch.sh
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

INPUT_DIR="${INPUT_DIR:-demo_results_parallel/g1/robot_only/custom_optitrack}"
OUTPUT_DIR="${OUTPUT_DIR:-converted_bm_g1/custom_optitrack}"
OUTPUT_FPS="${OUTPUT_FPS:-50}"
INPUT_FPS="${INPUT_FPS:-30}"
ROBOT="${ROBOT:-g1}"
mkdir -p "${OUTPUT_DIR}"

for f in "${INPUT_DIR}"/*.npz; do
  [ -f "$f" ] || continue
  stem=$(basename "$f" .npz)
  short="${stem%% *}"
  out="${OUTPUT_DIR}/${short}.npz"
  echo "Converting: $f -> $out"
  python data_conversion/convert_data_format_mj.py \
    --input-file "$f" \
    --output-name "$out" \
    --data-format optitrack \
    --robot-xml-path "models/${ROBOT}/${ROBOT}_29dof_convert.xml" \
    --output-format bm \
    --robot "${ROBOT}" \
    --object-name ground \
    --headless \
    --once \
    --output-fps "${OUTPUT_FPS}" \
    --input-fps "${INPUT_FPS}" \
    "$@"
done

echo "Batch export done. Output dir: ${OUTPUT_DIR}"
