#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_isaacsim_setup.sh"
cd "${REPO_ROOT}"

# Replay trained policy from local training logs.
RUN_DIR=${RUN_DIR:-/home/humanoid/wjs/Adam/holosoma/logs/WholeBodyTracking/20260215_072504-adam_pro_29dof_wbt-locomotion}
CHECKPOINT=${CHECKPOINT:-}

if [[ -z "${CHECKPOINT}" ]]; then
  CHECKPOINT=$(ls -1 "${RUN_DIR}"/model_*.pt 2>/dev/null | sort | tail -n 1 || true)
fi

if [[ -z "${CHECKPOINT}" ]]; then
  echo "No checkpoint found. Set RUN_DIR or CHECKPOINT explicitly." >&2
  exit 1
fi

## adam_pro_wbt_eval_latest_checkpoint
python src/holosoma/holosoma/eval_agent.py \
  --checkpoint="${CHECKPOINT}" \
  --training.headless=False \
  --training.num_envs=4 \
  "$@"

## replay_motion_clip_only
# python src/holosoma/holosoma/replay.py \
#   exp:adam-pro-29dof-wbt \
#   simulator:isaacsim \
#   --training.headless=False \
#   --training.num_envs=1 \
#   "$@"
