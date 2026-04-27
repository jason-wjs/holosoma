#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)
source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting"

ROBOT_XML="${ROBOT_XML:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/controller/mjlab/src/mjlab/asset_zoo/robots/unitree_g1/xmls/g1.xml}"
OUTPUT_FPS="${OUTPUT_FPS:-50}"

## platform_001
# python -m holosoma_retargeting.data_conversion.convert_data_format_parc_mj \
#   --input-file /tmp/parc_process_workspace/retargeted/platform_001_original.npz \
#   --output-name /tmp/tt_converted/platform_001/motion.npz \
#   --robot-xml "${ROBOT_XML}" \
#   --output-fps "${OUTPUT_FPS}" \
#   "$@"

## mid_blocks_004_dm
python -m holosoma_retargeting.data_conversion.convert_data_format_parc_mj \
  --input-file /tmp/parc_process_workspace/retargeted/mid_blocks_004_dm_original.npz \
  --output-name /tmp/tt_converted/mid_blocks_004_dm/motion.npz \
  --robot-xml "${ROBOT_XML}" \
  --output-fps "${OUTPUT_FPS}" \
  "$@"
