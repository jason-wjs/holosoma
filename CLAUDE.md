# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Holosoma is a comprehensive humanoid robotics framework for training and deploying reinforcement learning policies on humanoid robots, developed by Amazon's FAR (Field Autonomy and Robotics) team. It supports:

- **Multi-simulator training**: IsaacGym, IsaacSim, MJWarp (MuJoCo Warp), and MuJoCo (inference only)
- **Multiple RL algorithms**: PPO and FastSAC
- **Robot support**: Unitree G1, Booster T1, and Adam Pro humanoids
- **WBT support**: Unitree G1, Booster T1, and Adam Pro humanoids (Adam Pro support added in February 2026)
- **Task types**: Locomotion (velocity tracking) and whole-body tracking (WBT)
- **End-to-end pipeline**: From training to deployment (sim-to-sim and sim-to-real)
- **Motion retargeting**: Converting human motion capture data to robot motions

## Repository Structure

The project is organized as a **three-package monorepo**:

```
src/
├── holosoma/              # Core training framework
│   ├── holosoma/
│   │   ├── agents/        # PPO and FastSAC algorithm implementations
│   │   ├── config_types/  # Tyro configuration type definitions
│   │   ├── config_values/ # Experiment preset configurations
│   │   ├── envs/          # Task environments (locomotion, WBT)
│   │   ├── managers/      # Modular managers (action, observation, reward, etc.)
│   │   ├── simulator/     # Simulator abstractions (IsaacGym, IsaacSim, MJWarp)
│   │   └── bridge/        # Robot SDK bridges (unitree, booster)
│   └── setup.py
├── holosoma_inference/    # Inference and deployment pipeline
│   ├── holosoma_inference/
│   │   ├── bridge/        # Robot SDK bridges for inference
│   │   └── controllers/   # Control loops and policy execution
│   └── setup.py
└── holosoma_retargeting/  # Motion retargeting
    └── holosoma_retargeting/
        └── setup.py
```

## Development Setup

### Environment Setup

The project uses simulator-specific setup scripts that create isolated Python environments:

```bash
# For IsaacGym training
bash scripts/setup_isaacgym.sh

# For IsaacSim training (requires Ubuntu 22.04+)
bash scripts/setup_isaacsim.sh

# For MJWarp training and MuJoCo simulation (inference)
bash scripts/setup_mujoco.sh

# For inference/deployment only
bash scripts/setup_inference.sh

# For motion retargeting
bash scripts/setup_retargeting.sh
```

Each setup script creates a virtual environment in `.venv_<simulator>` and installs dependencies.

### Activating Environments

After setup, activate the appropriate environment:

```bash
source scripts/source_isaacgym_setup.sh   # or source_isaacsim_setup.sh, source_mujoco_setup.sh, etc.
```

### Pre-commit Hooks

Install pre-commit hooks before development:

```bash
pre-commit install
```

This configures Ruff (linting and formatting), Mypy (type checking), and clang-format (C/C++ files).

## Training

### Configuration System

Training uses **Tyro** for CLI arguments with hierarchical configuration. Experiment presets are defined using the `exp:` prefix:

```bash
# List all available experiments
python src/holosoma/holosoma/train_agent.py --help

# Example: G1 with FastSAC
python src/holosoma/holosoma/train_agent.py \
    exp:g1-29dof-fast-sac \
    simulator:isaacgym \
    logger:wandb \
    --training.seed 1
```

### Experiment Presets

Available experiment presets (in `holosoma/config_values/experiment.py`):

**Locomotion (Velocity Tracking):**
- `exp:g1-29dof` - G1 with PPO
- `exp:g1-29dof-fast-sac` - G1 with FastSAC
- `exp:t1-29dof` - T1 with PPO
- `exp:t1-29dof-fast-sac` - T1 with FastSAC

**Whole-Body Tracking:**
- `exp:g1-29dof-wbt` - G1 WBT with PPO
- `exp:g1-29dof-wbt-fast-sac` - G1 WBT with FastSAC
- `exp:g1-29dof-wbt-w-object` - G1 WBT with objects, PPO
- `exp:g1-29dof-wbt-fast-sac-w-object` - G1 WBT with objects, FastSAC
- `exp:adam-pro-29dof-wbt` - Adam Pro WBT with PPO
- `exp:adam-pro-29dof-wbt-fast-sac` - Adam Pro WBT with FastSAC

### Multi-GPU Training

Use PyTorch DDP for multi-GPU training:

```bash
torchrun --nproc_per_node=4 src/holosoma/holosoma/train_agent.py \
    exp:t1-29dof-fast-sac \
    simulator:isaacgym
```

### Simulator-specific Notes

- **IsaacGym**: Requires headless configuration for servers without display
- **IsaacSim**: Requires Ubuntu 22.04+; has more realistic physics but is heavier
- **MJWarp**: Beta support; uses `nconmax=96` by default (adjustable via `--simulator.config.mujoco-warp.nconmax-per-env`)
- **T1 with PPO on MJWarp**: Use `--terrain.terrain-term.scale-factor=0.5` to avoid training instabilities

### Video Recording

Video recording is enabled by default with `logger:wandb`. On headless servers, you may need to disable video or configure rendering (see `src/holosoma/README.md` for details).

## Testing

### Test Structure

- **CI tests**: `tests/ci/isaacgym_ci_tests.sh`, `tests/ci/isaacsim_ci_tests.sh`
- **E2E tests**: `tests/e2e/`
- **Nightly tests**: `tests/nightly/`
- **Unit tests**: Distributed throughout the codebase (e.g., `agents/modules/tests/`)

### Running Tests

```bash
# Run CI tests for specific simulator
bash tests/ci/isaacgym_ci_tests.sh

# Pytest with markers
pytest -m "not isaacsim"  # Skip IsaacSim tests
pytest -m "multi_gpu"     # Multi-GPU tests only
```

## Inference and Deployment

After training, deploy policies using the inference package. See `src/holosoma_inference/README.md` for detailed workflows:

- **Real Robot Locomotion**: `src/holosoma_inference/docs/workflows/real-robot-locomotion.md`
- **Real Robot WBT**: `src/holosoma_inference/docs/workflows/real-robot-wbt.md`
- **Sim-to-Sim Locomotion**: `src/holosoma_inference/docs/workflows/sim-to-sim-locomotion.md`
- **Sim-to-Sim WBT**: `src/holosoma_inference/docs/workflows/sim-to-sim-wbt.md`

### Loading ONNX Checkpoints

ONNX checkpoints are automatically exported during training. Load them directly from Wandb:

```bash
--task.model-path wandb://entity/project_name/run_id/model.onnx
```

### Policy Controls

Keyboard controls for policies (entered in the policy terminal):
- Start/stop policy: `]` / `o`
- Set robot to default pose: `i`
- Locomotion: `w` `a` `s` `d` for linear velocity, `q` `e` for angular velocity, `=` to switch walking/standing
- WBT: `s` to start motion clip

## Architecture

### Configuration System

- **Types**: `config_types/` - Define Tyro configuration dataclasses
- **Values**: `config_values/` - Provide preset values for specific robots/tasks
- **Resolvers**: Dynamic configuration resolution via OmegaConf
- **CLI**: `train_agent.py` is the entry point with `exp:` presets

### Simulator Abstraction

The framework provides a **unified interface** across simulators:
- Each simulator has its own backend in `simulator/isaacgym/`, `simulator/isaacsim/`, `simulator/mjwarp/`
- Common API through `envs/base_task/` and task-specific managers (`locomotion/`, `wbt/`)
- Cross-simulator evaluation: train in one simulator, evaluate in another

### Manager System

The framework uses a **modular manager pattern** for extensibility:
- **Action Manager**: Control mode (PD, position, velocity)
- **Observation Manager**: Sensor readings, state estimation
- **Reward Manager**: Reward terms and scaling
- **Curriculum Manager**: Task progression and difficulty
- **Termination Manager**: Episode termination conditions
- **Randomization Manager**: Domain randomization

Each manager is composed of "terms" that can be configured independently via YAML-style CLI args.

### Robot SDK Abstraction

Robot communication is abstracted through **bridge entry points**:

```python
# Defined in setup.py
entry_points={
    "holosoma.bridge": [
        "unitree = holosoma.bridge.unitree:UnitreeSdk2Bridge",
        "booster = holosoma.bridge.booster:BoosterSdk2Bridge",
    ],
}
```

Robot SDKs are dynamically downloaded from GitHub releases during installation:
- **Unitree**: `https://github.com/amazon-far/unitree_sdk2`
- **Booster**: `https://github.com/amazon-far/booster_robotics_sdk`

### Policy Pipeline

1. **Training**: RL policies trained in simulators (IsaacGym/IsaacSim/MJWarp)
2. **Export**: Automatic ONNX conversion during training
3. **Deployment**: ONNX policies deployed to real robots or MuJoCo
4. **Control**: Real-time control with configurable gains through `holosoma_inference`

## Code Quality

- **Linter**: Ruff with comprehensive configuration (see `pyproject.toml`)
- **Formatter**: Ruff format (120 character line length)
- **Type checker**: Mypy 1.14.1 (pinned, excluded from `holosoma_inference/`)
- **C/C++ formatter**: clang-format
- **Line endings**: LF enforced by pre-commit hooks

## Demo Scripts

End-to-end demo workflows are provided in `demo_scripts/`:

```bash
# OMOMO data: retargeting + WBT training
bash demo_scripts/demo_omomo_wb_tracking.sh

# LAFAN data: retargeting + WBT training
bash demo_scripts/demo_lafan_wb_tracking.sh
```

## Motion Retargeting

The retargeting package (`holosoma_retargeting`) converts human motion capture data to robot motions.

### Supported Data Formats

- **SMPL-H**: Whole-body motion with hands (from OMOMO, InterMimic)
- **LAFAN**: BVH-based motion data (requires conversion to `.npy`)
- **SMPL-X**: AMASS dataset format (requires conversion)
- **OptiTrack**: Custom `.pkl` format from motion capture sessions

### Retargeting Task Types

- `robot_only`: Retarget human motion to robot without objects/terrain
- `object_interaction`: Preserve interactions with objects (boxes, tools)
- `climbing`: Terrain interaction with climbing motions

### Bash Script Entry Points

Convenient scripts are provided in `scripts/retargeting/` for common workflows:

```bash
# Single clip retargeting (default: OptiTrack + Adam Pro)
bash scripts/retargeting/retarget_single_clip.sh

# Batch retargeting (default: Adam Pro, OptiTrack)
bash scripts/retargeting/retarget_batch_clips.sh

# Replay retargeted result in Viser
bash scripts/retargeting/replay_viser.sh

# Quantitative evaluation (default: Adam Pro, robot_only, OMOMO)
bash scripts/retargeting/eval.sh

# Data conversion scripts
bash scripts/retargeting/convert_lafan_bvh_to_npy.sh
bash scripts/retargeting/convert_amass_smplx_to_npz.sh
bash scripts/retargeting/convert_optitrack_pkl_to_npz.sh
```

Override default settings with environment variables:
```bash
ROBOT=g1 DATA_FORMAT=optitrack DATA_DIR=demo_data/optitrack_npz \
SAVE_DIR=demo_results_parallel/g1/robot_only/optitrack \
bash scripts/retargeting/retarget_batch_clips.sh
```

### Viser Visualization

Visualize retargeted results using the Viser player:
```bash
# Robot-only results
python src/holosoma_retargeting/holosoma_retargeting/viser_player.py \
    --robot_urdf models/g1/g1_29dof.urdf \
    --qpos_npz demo_results_parallel/g1/robot_only/omomo/sub3_largebox_003_original.npz

# Object-interaction results
python src/holosoma_retargeting/holosoma_retargeting/viser_player.py \
    --robot_urdf models/g1/g1_29dof.urdf \
    --object_urdf models/largebox/largebox.urdf \
    --qpos_npz demo_results_parallel/g1/object_interaction/omomo/sub3_largebox_003_original.npz
```

## Important Constraints

- **IsaacSim**: Requires Ubuntu 22.04 or later
- **MJWarp**: Beta support; Warp-lang pinned to version 1.10.0
- **Robot SDKs**: Platform-specific wheels (x86_64 and aarch64 supported)
- **Headless rendering**: Requires special configuration for video recording on servers without display
- **Adam Pro retargeting**: Hand end-effector markers are under refinement; for robot-only mode, rely on wrist-based behavior and ignore hand EE markers
