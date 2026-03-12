#!/usr/bin/env bash
# Filter optitrack NPZ by max velocity (default 5 m/s).
# Excluded files (max > threshold) are recorded; passed files are copied to optitrack_filter/.
#
# Usage:
#   bash scripts/retargeting/filter_optitrack_by_velocity.sh
#   THRESHOLD=10.0 bash scripts/retargeting/filter_optitrack_by_velocity.sh
#   bash scripts/retargeting/filter_optitrack_by_velocity.sh --dry-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INPUT_DIR="${INPUT_DIR:-$REPO_ROOT/src/holosoma_retargeting/holosoma_retargeting/converted_bm/optitrack}"

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "$REPO_ROOT/src/holosoma_retargeting/holosoma_retargeting"

python data_conversion/filter_optitrack_by_velocity.py \
    --input-dir "$INPUT_DIR" \
    --threshold "${THRESHOLD:-10.0}" \
    "$@"
