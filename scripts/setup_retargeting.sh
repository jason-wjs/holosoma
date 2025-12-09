# Exit on error, and print commands
set -ex

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(dirname "$SCRIPT_DIR")

# Create overall workspace
source ${SCRIPT_DIR}/source_common.sh
SENTINEL_FILE=${WORKSPACE_DIR}/.env_setup_retargeting

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

ENV_ROOT=$CONDA_ROOT/envs/hsretargeting

if [[ ! -f $SENTINEL_FILE ]]; then
  # Create the conda environment
  if [[ ! -d $ENV_ROOT ]]; then
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
    $CONDA_ROOT/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
    $CONDA_ROOT/bin/conda install -y mamba -c conda-forge -n base
    MAMBA_ROOT_PREFIX=$CONDA_ROOT $CONDA_ROOT/bin/mamba create -y -n hsretargeting python=3.11 -c conda-forge --override-channels
  fi

  source $CONDA_ROOT/bin/activate hsretargeting

  # Install holosoma_retargeting
  pip install -U pip
  pip install -e $ROOT_DIR/src/holosoma_retargeting
  touch $SENTINEL_FILE
fi
