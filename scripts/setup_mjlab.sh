#!/bin/bash
# Acceptance criteria:
# - Creates/updates hsmjlab conda environment by default
# - Uses Python 3.11 by default
# - Installs holosoma editable package in no-deps mode
# - Installs pinned mjlab==1.1.1 (no local-source mode)
# - Verifies import mjlab and prints version
# - Verifies import holosoma in the same environment
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")

ENV_NAME="hsmjlab"
PYTHON_VERSION="3.11"
FORCE_RECREATE=0

usage() {
  cat <<EOF
Usage: $0 [--env-name NAME] [--python VERSION] [--force-recreate]

Options:
  --env-name NAME       Conda environment name (default: hsmjlab)
  --python VERSION      Python version (default: 3.11)
  --force-recreate      Remove and recreate the target conda environment
  --help, -h            Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-name)
      ENV_NAME="${2:-}"
      shift 2
      ;;
    --python)
      PYTHON_VERSION="${2:-}"
      shift 2
      ;;
    --force-recreate)
      FORCE_RECREATE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$ENV_NAME" ]]; then
  echo "Environment name cannot be empty." >&2
  exit 1
fi

if [[ -z "$PYTHON_VERSION" ]]; then
  echo "Python version cannot be empty." >&2
  exit 1
fi

source "${SCRIPT_DIR}/source_common.sh"

ENV_ROOT="${CONDA_ROOT}/envs/${ENV_NAME}"
SENTINEL_FILE="${WORKSPACE_DIR}/.env_setup_finished_${ENV_NAME}_mjlab"
mkdir -p "${WORKSPACE_DIR}"

check_env_health() {
  if [[ ! -d "${ENV_ROOT}" ]]; then
    return 1
  fi

  source "${CONDA_ROOT}/bin/activate" "${ENV_NAME}"
  python - <<'PY'
import importlib.util
import sys

required_modules = ["mjlab", "holosoma"]
missing = [m for m in required_modules if importlib.util.find_spec(m) is None]
if missing:
    print("Missing required modules:", ", ".join(missing))
    sys.exit(1)

import mjlab
print("mjlab version:", mjlab.__version__)
PY
}

if [[ ! -d "${CONDA_ROOT}" ]]; then
  mkdir -p "${CONDA_ROOT}"
  OS_NAME="$(uname -s)"
  ARCH_NAME="$(uname -m)"

  if [[ "${OS_NAME}" == "Linux" ]]; then
    MINICONDA_INSTALLER="Miniconda3-latest-Linux-x86_64.sh"
  elif [[ "${OS_NAME}" == "Darwin" ]]; then
    if [[ "${ARCH_NAME}" == "arm64" ]]; then
      MINICONDA_INSTALLER="Miniconda3-latest-MacOSX-arm64.sh"
    else
      MINICONDA_INSTALLER="Miniconda3-latest-MacOSX-x86_64.sh"
    fi
  else
    echo "Unsupported OS: ${OS_NAME}" >&2
    exit 1
  fi

  curl "https://repo.anaconda.com/miniconda/${MINICONDA_INSTALLER}" -o "${CONDA_ROOT}/miniconda.sh"
  bash "${CONDA_ROOT}/miniconda.sh" -b -u -p "${CONDA_ROOT}"
  rm -f "${CONDA_ROOT}/miniconda.sh"
fi

if [[ "${FORCE_RECREATE}" -eq 1 ]]; then
  rm -f "${SENTINEL_FILE}"
  if [[ -d "${ENV_ROOT}" ]]; then
    "${CONDA_ROOT}/bin/conda" env remove -y -n "${ENV_NAME}"
  fi
fi

if [[ -f "${SENTINEL_FILE}" ]]; then
  if check_env_health; then
    echo "Environment already healthy; skipping setup."
    exit 0
  fi
  rm -f "${SENTINEL_FILE}"
fi

if [[ ! -d "${ENV_ROOT}" ]]; then
  "${CONDA_ROOT}/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
  "${CONDA_ROOT}/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
  if [[ ! -x "${CONDA_ROOT}/bin/mamba" ]]; then
    "${CONDA_ROOT}/bin/conda" install -y mamba -c conda-forge -n base
  fi
  MAMBA_ROOT_PREFIX="${CONDA_ROOT}" "${CONDA_ROOT}/bin/mamba" create -y -n "${ENV_NAME}" \
    "python=${PYTHON_VERSION}" -c conda-forge --override-channels
fi

source "${CONDA_ROOT}/bin/activate" "${ENV_NAME}"

pip install --upgrade pip

# Install pinned mjlab release from package index only (no local-source mode).
pip install "mjlab==1.1.1" \
  --extra-index-url https://pypi.nvidia.com \
  --extra-index-url https://download.pytorch.org/whl/cu128 \
  --extra-index-url https://py.mujoco.org

# Install holosoma package for local development without overriding mjlab dependency versions.
pip install -e "${ROOT_DIR}/src/holosoma" --no-deps

python - <<'PY'
import mjlab
import holosoma
print("mjlab version:", mjlab.__version__)
print("holosoma import: OK")
PY

touch "${SENTINEL_FILE}"
echo "MJLAB environment setup completed: ${ENV_NAME}"
