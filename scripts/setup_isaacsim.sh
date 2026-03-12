# Exit on error, and print commands
set -ex

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(dirname "$SCRIPT_DIR")

# Use CONDA_ENV_NAME if provided, otherwise default to "hssim"
CONDA_ENV_NAME=${CONDA_ENV_NAME:-hssim}
echo "conda environment name is set to: $CONDA_ENV_NAME"
ISAACSIM_VERSION=${ISAACSIM_VERSION:-5.1.0}
ISAACLAB_REF=${ISAACLAB_REF:-v2.3.0}
ISAACLAB_RL_FRAMEWORK=${ISAACLAB_RL_FRAMEWORK:-rsl_rl}
echo "Isaac Sim version is set to: $ISAACSIM_VERSION"
echo "IsaacLab ref is set to: $ISAACLAB_REF"
echo "IsaacLab RL framework is set to: $ISAACLAB_RL_FRAMEWORK"

# Create overall workspace
source ${SCRIPT_DIR}/source_common.sh
ENV_ROOT=$CONDA_ROOT/envs/$CONDA_ENV_NAME
SENTINEL_FILE=${WORKSPACE_DIR}/.env_setup_finished_$CONDA_ENV_NAME
echo "SENTINEL_FILE: $SENTINEL_FILE"

mkdir -p $WORKSPACE_DIR

check_env_health() {
  if [[ ! -d $ENV_ROOT ]]; then
    return 1
  fi
  source $CONDA_ROOT/bin/activate $CONDA_ENV_NAME
  python - <<'PY'
import importlib.util
import sys

required_modules = [
    "isaacsim",
    "isaaclab",
    "tyro",
    "loguru",
    "easydict",
    "rich",
    "termcolor",
    "holosoma",
]
missing_modules = [m for m in required_modules if importlib.util.find_spec(m) is None]
if missing_modules:
    print("Environment health check failed; missing modules:", ", ".join(missing_modules))
    sys.exit(1)
print("Environment health check passed.")
PY
}

check_isaaclab_ref() {
  if [[ ! -d $WORKSPACE_DIR/IsaacLab/.git ]]; then
    return 1
  fi
  local expected_sha
  local current_sha
  expected_sha=$(git -C "$WORKSPACE_DIR/IsaacLab" rev-parse "$ISAACLAB_REF" 2>/dev/null || true)
  if [[ -z $expected_sha ]]; then
    return 1
  fi
  current_sha=$(git -C "$WORKSPACE_DIR/IsaacLab" rev-parse HEAD)
  [[ "$current_sha" == "$expected_sha" ]]
}

if [[ -f $SENTINEL_FILE ]]; then
  if check_env_health && check_isaaclab_ref; then
    echo "Environment already healthy; skipping setup."
    exit 0
  fi
  echo "Sentinel exists but environment is stale or mismatched. Re-running setup."
  rm -f "$SENTINEL_FILE"
fi

if [[ ! -f $SENTINEL_FILE ]]; then
  # Install miniconda
  if [[ ! -d $CONDA_ROOT ]]; then
    mkdir -p $CONDA_ROOT
    curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o $CONDA_ROOT/miniconda.sh
    bash $CONDA_ROOT/miniconda.sh -b -u -p $CONDA_ROOT
    rm $CONDA_ROOT/miniconda.sh
  fi

  # Create the conda environment
  if [[ ! -d $ENV_ROOT ]]; then
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
    if [[ ! -f $CONDA_ROOT/bin/mamba ]]; then
      $CONDA_ROOT/bin/conda install -y mamba -c conda-forge -n base
    fi
    MAMBA_ROOT_PREFIX=$CONDA_ROOT $CONDA_ROOT/bin/mamba create -y -n $CONDA_ENV_NAME python=3.11 -c conda-forge --override-channels
  fi

  source $CONDA_ROOT/bin/activate $CONDA_ENV_NAME

  # Install ffmpeg for video encoding
  conda install -c conda-forge -y ffmpeg
  conda install -c conda-forge -y libiconv
  conda install -c conda-forge -y libglu

  # Below follows https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/pip_installation.html
  # Install IsaacSim
  pip install --upgrade pip
  pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

  # Install dependencies from PyPI first
  pip install pyperclip
  # Then install isaacsim from NVIDIA index only
  pip install "isaacsim[all,extscache]==${ISAACSIM_VERSION}" --extra-index-url https://pypi.nvidia.com

  if [[ ! -d $WORKSPACE_DIR/IsaacLab ]]; then
    git clone https://github.com/isaac-sim/IsaacLab.git --branch "$ISAACLAB_REF" $WORKSPACE_DIR/IsaacLab
  else
    if [[ ! -d $WORKSPACE_DIR/IsaacLab/.git ]]; then
      echo "ERROR: $WORKSPACE_DIR/IsaacLab exists but is not a git repository."
      echo "Please remove it or run scripts/reset_isaacsim.sh and re-run setup."
      exit 1
    fi
    # Keep an existing checkout aligned with the configured IsaacLab ref.
    git -C "$WORKSPACE_DIR/IsaacLab" fetch --tags origin
    git -C "$WORKSPACE_DIR/IsaacLab" checkout "$ISAACLAB_REF"
  fi

  if command -v cmake >/dev/null 2>&1 && command -v make >/dev/null 2>&1; then
    echo "Build tools already available; skipping apt install."
  elif command -v apt >/dev/null 2>&1; then
    if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
      apt install -y cmake build-essential
    elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
      sudo apt install -y cmake build-essential
    else
      echo "WARNING: cmake/build-essential are required but apt install needs interactive sudo."
      echo "Please run: sudo apt install -y cmake build-essential"
      exit 1
    fi
  else
    echo "WARNING: apt not available; please ensure cmake and build-essential are installed."
  fi
  cd $WORKSPACE_DIR/IsaacLab
  # work-around for egl_probe cmake max version issue
  export CMAKE_POLICY_VERSION_MINIMUM=3.5
  # Pre-install flatdict without build isolation to avoid pkg_resources error
  pip install --no-build-isolation flatdict
  # IsaacLab v2.3.0 accepts a single framework selector for --install.
  ./isaaclab.sh --install "$ISAACLAB_RL_FRAMEWORK"

 # Install Holosoma
  pip install -U pip
  pip install -e $ROOT_DIR/src/holosoma[unitree,booster]

  # Keep wandb aligned with holosoma's pinned dependency.
  pip install --upgrade 'wandb==0.22.0'
  touch $SENTINEL_FILE
fi