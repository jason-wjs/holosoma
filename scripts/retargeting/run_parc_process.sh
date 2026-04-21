#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)
source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

## platform_001
python examples/parc_process.py \
  --sample /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl \
  --source-xml /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml \
  --output-root /tmp/parc_process_bootstrap \
  --retarget-save-dir /tmp/parc_process_workspace \
  "$@"

## mid_blocks_004_dm
# python examples/parc_process.py \
#   --sample /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/mid_climbing/mid_blocks_004_dm.pkl \
#   --source-xml /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml \
#   --output-root /tmp/parc_process_bootstrap \
#   --retarget-save-dir /tmp/parc_process_workspace \
#   "$@"

## beyond_platform_002
# python examples/parc_process.py \
#   --sample /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/beyond_platform_002.pkl \
#   --source-xml /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml \
#   --output-root /tmp/parc_process_bootstrap_more \
#   --retarget-save-dir /tmp/parc_process_workspace_more \
#   "$@"

## batch via manifest
# python examples/parc_process.py \
#   --manifest /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/parc_manifest.yaml \
#   --source-xml /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml \
#   --output-root /tmp/parc_process_bootstrap_batch \
#   --retarget-save-dir /tmp/parc_process_workspace_batch \
#   "$@"


