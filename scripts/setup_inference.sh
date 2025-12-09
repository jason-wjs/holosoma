# Exit on error, and print commands
set -ex

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(dirname "$SCRIPT_DIR")

echo "Setting up inference environment"

OS=$(uname -s)
ARCH=$(uname -m)

case $ARCH in
  "aarch64"|"arm64") ARCH="aarch64" ;;
  "x86_64") ARCH="x86_64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

case $OS in
  "Linux")
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${ARCH}.sh"
    PACKAGE_MANAGER="apt-get"
    INSTALL_CMD="sudo apt-get install -y"
    ;;
  "Darwin")
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    PACKAGE_MANAGER="brew"
    INSTALL_CMD="brew install"
    ;;
  *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

# Create overall workspace
source ${SCRIPT_DIR}/source_common.sh
SENTINEL_FILE=${WORKSPACE_DIR}/.env_setup_finished_inference

mkdir -p $WORKSPACE_DIR

# Detect existing conda installation
if command -v conda &> /dev/null; then
  # Use conda from PATH
  CONDA_BIN=$(which conda)
  CONDA_ROOT=$(dirname $(dirname $CONDA_BIN))
elif [[ -d "$HOME/miniconda3" ]]; then
  # Use miniconda3 in home directory
  CONDA_ROOT="$HOME/miniconda3"
elif [[ -d "$HOME/anaconda3" ]]; then
  # Use anaconda3 in home directory
  CONDA_ROOT="$HOME/anaconda3"
else
  echo "Error: Could not find conda installation. Please ensure conda is in PATH or installed at $HOME/miniconda3"
  exit 1
fi

ENV_ROOT=$CONDA_ROOT/envs/hsinference

if [[ ! -f $SENTINEL_FILE ]]; then
  # Install swig based on OS
  if [[ $OS == "Linux" ]]; then
    $INSTALL_CMD swig
  elif [[ $OS == "Darwin" ]]; then
    # Install brew if needed
    if ! command -v brew &> /dev/null; then
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      echo >> $HOME/.zprofile
      echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    $INSTALL_CMD swig
  fi

  # Create the conda environment
  if [[ ! -d $ENV_ROOT ]]; then
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
    $CONDA_ROOT/bin/conda install -y mamba -c conda-forge -n base
    MAMBA_ROOT_PREFIX=$CONDA_ROOT $CONDA_ROOT/bin/mamba create -y -n hsinference python=3.10 -c conda-forge --override-channels
  fi

  source $CONDA_ROOT/bin/activate hsinference

  # Install libstdcxx-ng to fix the error: `version `GLIBCXX_3.4.32' not found` on Ubuntu 24.04
  conda install -c conda-forge -y libstdcxx-ng

  # Install holosoma_inference
  pip install -e $ROOT_DIR/src/holosoma_inference[unitree,booster]

  # Setup a few things for ARM64 Linux (G1 Jetson)
  # Otherwise we get this error:
  # /opt/rh/gcc-toolset-14/root/usr/include/c++/14/bits/stl_vector.h:1130: ...
  if [[ $OS == "Linux" && $ARCH == "aarch64" ]]; then
    sudo nvpmodel -m 0 2>/dev/null || true
    pip install pin>=3.8.0
  else
    if [[ ! -d $WORKSPACE_DIR/unitree_sdk2_python ]]; then
      git clone https://github.com/unitreerobotics/unitree_sdk2_python.git $WORKSPACE_DIR/unitree_sdk2_python
    fi
    pip install -e $WORKSPACE_DIR/unitree_sdk2_python/
    $CONDA_ROOT/bin/conda install pinocchio -y -c conda-forge --override-channels
  fi

  cd $ROOT_DIR
  touch $SENTINEL_FILE
fi
