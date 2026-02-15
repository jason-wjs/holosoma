#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_isaacsim_setup.sh"
cd "${REPO_ROOT}"

# Explicit W&B routing (hardcoded to jason-wjs).
WANDB_ENTITY=${WANDB_ENTITY:-jason-wjs-shanghai-jiao-tong-university}
WANDB_PROJECT=${WANDB_PROJECT:-holosoma}

if [[ -z "${WANDB_API_KEY:-}" ]]; then
  echo "WANDB_API_KEY is not set. Export it before running training." >&2
  exit 1
fi

## adam_pro_wbt_ppo_default
python src/holosoma/holosoma/train_agent.py \
  exp:adam-pro-29dof-wbt \
  simulator:isaacsim \
  logger:wandb \
  --logger.entity="${WANDB_ENTITY}" \
  --logger.project="${WANDB_PROJECT}" \
  --training.headless=True \
  --training.num_envs=4096 \
  --command.setup_terms.motion_command.params.motion_config.motion_file="/home/humanoid/wjs/Adam/holosoma/src/holosoma/holosoma/data/motions/adam_pro_29dof/whole_body_tracking/lafan1/dance1_subject1_mj_fps50.npz" \
  "$@"

## adam_pro_wbt_fast_sac
# python src/holosoma/holosoma/train_agent.py \
#   exp:adam-pro-29dof-wbt-fast-sac \
#   simulator:isaacsim \
#   logger:wandb \
#   --logger.entity="${WANDB_ENTITY}" \
#   --logger.project="${WANDB_PROJECT}" \
#   "$@"

