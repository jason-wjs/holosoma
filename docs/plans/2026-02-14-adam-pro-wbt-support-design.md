# Adam Pro Whole-Body Tracking Support - Design Document

**Date:** 2026-02-14
**Author:** Claude (AI Assistant)
**Status:** Approved

## Overview

Add Whole-Body Tracking (WBT) training support for the Adam Pro (29-DoF) humanoid robot in IsaacSim, following the existing G1 WBT configuration pattern. This is a straightforward shadowing of G1's WBT implementation with robot-specific adjustments.

**Scope:**
- Robot-only WBT training (no object interaction initially)
- IsaacSim simulator (default)
- PPO and FastSAC algorithm support
- Single motion file preset (extensible later)

**Out of Scope:**
- Object interaction (can add later following G1 pattern)
- IsaacSim locomotion support (locomotion remains MJWarp-only)
- New robot model files (URDF/XML already exist)

---

## Architecture

### Configuration Hierarchy

```
config_values/
├── robot.py                    # adam_pro_29dof RobotConfig (EXISTS)
├── experiment.py                # Registers new WBT presets
└── wbt/
    └── adam_pro/               # NEW DIRECTORY
        ├── __init__.py
        ├── action.py
        ├── command.py
        ├── curriculum.py
        ├── experiment.py
        ├── observation.py
        ├── randomization.py
        ├── reward.py
        └── termination.py
```

### Design Pattern

This implementation **shadows G1's WBT structure**:
1. Copy `config_values/wbt/g1/` directory structure
2. Replace `g1_29dof` references with `adam_pro_29dof`
3. Update robot-specific values (init height, body names, motion paths)
4. Add TODO comments for parameters requiring Adam Pro tuning

---

## Implementation Details

### 1. Robot Configuration

**Reuses existing config:** `robot.adam_pro_29dof` from `config_values/robot.py`

**Key robot properties:**
- DOF: 29 actuated joints
- Bodies: 58 total
- Init height: 0.90m (pelvis position, not total robot height)
- Total robot height: 1.67m
- Control: P-gain with robot-specific stiffness/damping

**Body naming convention (from URDF):**
- Joints: `hipPitch_Left`, `kneePitch_Left`, etc. (camelCase)
- Links: `left_hip_pitch_link`, `left_knee_link`, etc. (snake_case with `_link` suffix)

### 2. Experiment Presets

**File:** `config_values/wbt/adam_pro/experiment.py`

Two presets created:

**adam_pro_29dof_wbt** (PPO):
```python
ExperimentConfig(
    env_class="holosoma.envs.wbt.wbt_manager.WholeBodyTrackingManager",
    training=TrainingConfig(project="WholeBodyTracking", name="adam_pro_29dof_wbt"),
    algo=replace(algo.ppo, config=replace(algo.ppo.config,
        num_learning_iterations=40000,  # TODO: Tune based on motion length
        use_symmetry=False)),
    simulator=replace(simulator.isaacsim, ...),  # DEFAULT: ISAACSIM
    robot=replace(robot.adam_pro_29dof,
        control=replace(robot.adam_pro_29dof.control, action_scale=1.0),  # WBT uses 1.0
        asset=replace(robot.adam_pro_29dof.asset, enable_self_collisions=True),
        init_state=replace(robot.adam_pro_29dof.init_state,
            pos=[0.0, 0.0, 0.90])),  # ADAM PRO PELVIS HEIGHT
    ...
)
```

**adam_pro_29dof_wbt_fast_sac** (FastSAC):
```python
# Similar structure, FastSAC algorithm
# num_learning_iterations=400000
# gamma=0.99 (higher for motion tracking)
```

**Key differences from G1:**
- Robot config: `robot.adam_pro_29dof` (not `robot.g1_29dof`)
- Init height: `0.90m` (Adam Pro) vs `0.76m` (G1)
- Simulator: IsaacSim (same as G1 WBT)

### 3. Motion Data Configuration

**File:** `config_values/wbt/adam_pro/command.py`

**Motion file:** `holosoma/data/motions/adam_pro_29dof/whole_body_tracking/dance1_subject1_mj_fps50.npz`

**From actual retargeted file:**
- FPS: 50
- Body names (from motion file):
  ```python
  ['world', 'pelvis', 'pelvis_contour_link',
   'left_hip_pitch_link', 'left_hip_roll_link', 'left_hip_yaw_link', 'left_knee_link',
   'left_ankle_pitch_link', 'left_ankle_roll_link',
   'right_hip_pitch_link', 'right_hip_roll_link', 'right_hip_yaw_link', 'right_knee_link',
   'right_ankle_pitch_link', 'right_ankle_roll_link',
   'waist_yaw_link', 'waist_roll_link', 'torso_link', 'waist_support_link',
   'left_shoulder_pitch_link', 'left_shoulder_roll_link', 'left_shoulder_yaw_link',
   'left_elbow_link', 'left_wrist_roll_link', 'left_wrist_pitch_link', 'left_wrist_yaw_link',
   'right_shoulder_pitch_link', 'right_shoulder_roll_link', 'right_shoulder_yaw_link',
   'right_elbow_link', 'right_wrist_roll_link', 'right_wrist_pitch_link', 'right_wrist_yaw_link']
  ```
- Joint names (29): `left_hip_pitch_joint`, `left_hip_roll_joint`, etc.

**Body names to track:**
```python
motion_config = MotionConfig(
    motion_file=".../dance1_subject1_mj_fps50.npz",
    body_names_to_track=[
        "pelvis",
        "torso_link",
        # Left leg
        "left_hip_pitch_link", "left_knee_link", "left_ankle_roll_link",
        # Right leg
        "right_hip_pitch_link", "right_knee_link", "right_ankle_roll_link",
        # Left arm
        "left_shoulder_pitch_link", "left_elbow_link", "left_wrist_yaw_link",
        # Right arm
        "right_shoulder_pitch_link", "right_elbow_link", "right_wrist_yaw_link",
    ],
    body_name_ref=["torso_link"],  # Reference for relative pose computation
    use_adaptive_timesteps_sampler=True,  # Enable adaptive sampling
    noise_to_initial_pose=init_pose_config,
)
```

**Note:** Motion file path is **hardcoded** (matches G1 pattern), but CLI overrideable via:
```bash
--command.setup_terms.motion_command.params.motion_config.motion_file=/path/to/motion.npz
```

### 4. Action Configuration

**File:** `config_values/wbt/adam_pro/action.py`

```python
adam_pro_29dof_joint_pos = ActionManagerCfg(
    terms={
        "joint_control": ActionTermCfg(
            func="holosoma.managers.action.terms.joint_control:JointPositionActionTerm",
            params={},
            scale=1.0,  # WBT uses 1.0 (locomotion uses 0.25)
            clip=None,
        ),
    }
)
```

Identical to G1 WBT action config.

### 5. Observation Configuration

**File:** `config_values/wbt/adam_pro/observation.py`

**Structure matches G1 exactly:**
- Actor observations (6 terms): Target poses, base velocity, joint states, actions
- Critic observations (10 terms): All actor terms + full body poses + velocities
- Noise enabled for actor, disabled for critic
- Terms as **dict**, not list

**Actor observation terms:**
1. `motion_command` - Target joint positions/velocities
2. `motion_ref_ori_b` - Reference orientation in base frame
3. `base_ang_vel` - Base angular velocity
4. `dof_pos` - Joint positions
5. `dof_vel` - Joint velocities
6. `actions` - Previous actions

**Critic additional terms:**
7. `motion_ref_pos_b` - Reference position in base frame
8. `robot_body_pos_b` - Actual body positions
9. `robot_body_ori_b` - Actual body orientations
10. `base_lin_vel` - Base linear velocity

### 6. Reward Configuration

**File:** `config_values/wbt/adam_pro/reward.py`

**Reward terms (copied from G1 WBT):**

| Term | Weight | TODO Parameter |
|------|--------|----------------|
| `motion_global_ref_position_error_exp` | 1.0 | sigma=0.3 |
| `motion_global_ref_orientation_error_exp` | 1.0 | sigma=0.4 |
| `motion_relative_body_position_error_exp` | 2.0 | sigma=0.3 |
| `motion_relative_body_orientation_error_exp` | 2.0 | sigma=0.4 |
| `motion_global_body_lin_vel` | 1.0 | sigma=1.0 |
| `motion_global_body_ang_vel` | 0.5 | sigma=3.14 |
| `penalty_action_rate` | -0.1 | - |
| `limits_dof_pos` | -100.0 | tolerence=0.01 |
| `undesired_contacts` | -0.5 | max_force=1.0 |

**Reward function:** Exponential error kernel
```python
reward = weight * exp(-error / sigma)
```

**TODOs:**
- Sigma values affect tracking sensitivity (lower = stricter, higher = looser)
- Weights balance reward contributions
- Joint limit tolerance and contact thresholds may need Adam Pro tuning

### 7. Termination Configuration

**File:** `config_values/wbt/adam_pro/termination.py`

**Termination terms:**

1. `bad_ref_tracking` - Episode ends if tracking error exceeds thresholds
   - `ref_pos_error_threshold`: 0.5m (TODO)
   - `ref_ori_error_threshold`: 1.0rad (TODO)
   - `velocity_error_threshold`: 2.0m/s (TODO)

2. `bad_joint_pos_limits` - Episode ends if joint limits violated
   - `clip_limit_to_violation_ratio`: 0.98 (TODO: adjust for Adam Pro)

3. `bad_contact` - Episode ends on undesired contacts
   - `max_undesired_contact_force`: 200.0N (TODO: tune)
   - `max_contact_duration`: 0.1s

**Episode termination conditions:**
- Motion clip ends (automatic via MotionCommand)
- Tracking error exceeds thresholds (above)
- Joint limit violations (above)
- Undesired contacts (above)

### 8. Randomization Configuration

**File:** `config_values/wbt/adam_pro/randomization.py`

**Moderate domain randomization (matches G1 WBT):**

**Setup randomization:**
1. **Material properties** (friction, restitution)
   - Static friction: 0.3-1.6
   - Dynamic friction: 0.3-1.2
   - Restitution: 0.0-0.5

2. **Base COM offset**
   - x: ±2.5cm
   - y: ±5cm
   - z: ±5cm

3. **Joint position bias at startup**
   - Range: ±0.025rad

4. **Push perturbations**
   - Interval: Every 1-3 seconds
   - Velocities: Moderate (0.2-0.78 m/s)

5. **PD gain randomization**
   - kp: ±10%
   - kd: ±10%

**Reset randomization:**
- Joint position bias reapplied

**Step randomization:**
- Push forces applied

**Disabled:**
- Control delay (WBT focuses on motion tracking fidelity)

### 9. Curriculum Configuration

**File:** `config_values/wbt/adam_pro/curriculum.py`

**Adaptive timestep sampling:**
```python
adam_pro_29dof_wbt_curriculum = CurriculumManagerCfg(
    terms={
        "adaptive_sampling": TermCfg(
            func="holosoma.managers.curriculum.terms.wbt:adaptive_timestep_sampling",
            params={
                "num_bins": 30,  # 1-second bins for 50fps motion
                "kernel_std": 2.0,  # Smoothing for sampling distribution
            },
        ),
    },
)
```

**Purpose:** Prioritizes training on difficult motion segments by sampling failed timesteps more frequently.

**num_bins calculation:**
- Motion length: ~30s (estimated)
- FPS: 50
- Bins: 30 (1-second bins each)
- Frames per bin: ~50

Adjust `num_bins` if actual motion length differs significantly.

### 10. Registration

**File:** `config_values/wbt/adam_pro/__init__.py`

Export all configs:
```python
from holosoma.config_values.wbt.adam_pro.experiment import (
    adam_pro_29dof_wbt,
    adam_pro_29dof_wbt_fast_sac,
)
from holosoma.config_values.wbt.adam_pro.action import adam_pro_29dof_joint_pos
from holosoma.config_values.wbt.adam_pro.command import adam_pro_29dof_wbt_command
# ... etc

__all__ = [
    "adam_pro_29dof_wbt",
    "adam_pro_29dof_wbt_fast_sac",
    # ... all configs
]
```

**File:** `config_values/experiment.py`

Register presets in DEFAULTS:
```python
DEFAULTS = {
    # ... existing ...
    "adam_pro_29dof_wbt": adam_pro_29dof_wbt,
    "adam_pro_29dof_wbt_fast_sac": adam_pro_29dof_wbt_fast_sac,
}
```

---

## Files Summary

### New Files to Create: 8

```
config_values/wbt/adam_pro/
├── __init__.py          # 45 lines
├── action.py            # 17 lines
├── command.py           # 75 lines
├── curriculum.py        # 22 lines
├── experiment.py        # 130 lines (2 presets)
├── observation.py       # 90 lines
├── randomization.py     # 110 lines
├── reward.py            # 85 lines
└── termination.py       # 35 lines
```

**Total:** ~609 lines of config code

### Files to Modify: 2

1. `config_values/experiment.py` - Add 2 entries to DEFAULTS dict
2. No changes to robot config (reuses existing `robot.adam_pro_29dof`)

---

## Testing & Validation

### 1. Dry Run Test

```bash
python src/holosoma/holosoma/train_agent.py \
    exp:adam-pro-29dof-wbt \
    simulator:isaacsim \
    --training.num_learning_iterations 1 \
    --training.num_envs 256
```

**Verify:**
- Experiment preset loads
- Motion file loads successfully
- Environment initializes without errors
- Robot spawns at correct height (0.90m)

### 2. Short Training Run

```bash
python src/holosoma/holosoma/train_agent.py \
    exp:adam-pro-29dof-wbt \
    simulator:isaacsim \
    --training.num_learning_iterations 100 \
    --training.num_envs 1024
```

**Verify:**
- Episodes complete successfully
- Rewards compute (check tracking metrics)
- No NaN/Inf in observations or rewards
- ONNX export works
- WandB logging works

### 3. Cross-Simulator Validation (Optional)

```bash
# Train in IsaacSim, evaluate in MJWarp
python src/holosoma/holosoma/train_agent.py \
    exp:adam-pro-29dof-wbt \
    --task.model-path wandb://.../model.onnx \
    simulator:mujoco_warp
```

**Verify:**
- Policy loads in different simulator
- Evaluation runs without errors
- Tracking performance comparable

### 4. Training Metrics

**Key metrics to monitor:**
- `Episode/rew_motion_global_ref_position_error_exp` → Target: ~0.16
- `Episode/rew_motion_global_ref_orientation_error_exp` → Target: ~0.20
- `Episode/rew_motion_relative_body_position_error_exp` → Target: ~0.45
- `Episode/rew_motion_relative_body_orientation_error_exp` → Target: ~0.30
- `Episode/rew_motion_global_body_lin_vel` → Target: ~0.30
- `Episode/rew_motion_global_body_ang_vel` → Target: ~0.02

**Benchmarks from G1 WBT:**
- PPO converges in ~40k iterations
- FastSAC converges in ~400k iterations

---

## Future Extensions

### 1. Object Interaction

Follow `g1_29dof_wbt_w_object` pattern:

1. Create `robot.adam_pro_29dof_w_object` with object URDF path
2. Add object tracking observations/rewads
3. Create `adam_pro_29dof_wbt_w_object` experiment preset
4. Update randomization for object state

### 2. Additional Motion Files

**Option A:** New experiment presets per motion file
```python
adam_pro_29dof_wbt_dance2 = replace(adam_pro_29dof_wbt,
    command=command.adam_pro_29dof_wbt_command_dance2)
```

**Option B:** CLI override (no code changes)
```bash
python train_agent.py exp:adam-pro-29dof-wbt \
  --command.setup_terms.motion_command.params.motion_config.motion_file=/path/to/other.npz
```

### 3. IsaacSim Locomotion

Add to `config_values/loco/adam_pro/experiment.py`:
```python
adam_pro_29dof_isaacsim = replace(adam_pro_29dof,
    simulator=replace(simulator.isaacsim, ...))
adam_pro_29dof_fast_sac_isaacsim = replace(...)
```

Enables simulator comparison: MJWarp vs IsaacSim training quality.

---

## Design Decisions Rationale

### Q: Why IsaacSim default for WBT?
**A:** WBT requires accurate physics for motion tracking. IsaacSim provides more realistic contact dynamics than MJWarp. G1 follows this pattern (locomotion→IsaacGym, WBT→IsaacSim).

### Q: Why hardcode motion file path?
**A:** Matches G1's pattern. Simple and explicit. CLI override available for flexibility. Each experiment preset has a default motion file.

### Q: Why TODO placeholders instead of tuned values?
**A:** Adam Pro dynamics differ from G1 (different mass distribution, joint limits, actuator specs). Initial training will inform parameter tuning. G1 values provide reasonable starting point.

### Q: Why robot-only initially?
**A:** YAGNI principle. Robot-only tracking is core functionality. Object interaction can be added later following established pattern without breaking changes.

### Q: Why not add IsaacSim locomotion?
**A:** Out of scope for this task. Adam Pro locomotion already works in MJWarp. Can add IsaacSim as separate task if needed.

### Q: Why reuse `robot.adam_pro_29dof` config?
**A:** Single source of truth. Robot model files, joint limits, PD gains already configured. WBT only adjusts `action_scale` (1.0) and enables `self_collisions`.

---

## Acceptance Criteria

Implementation complete when:

- [ ] All 8 config files created under `config_values/wbt/adam_pro/`
- [ ] Experiment presets registered in `config_values/experiment.py`
- [ ] Dry run test passes without errors
- [ ] Motion file loads successfully
- [ ] Robot initializes at correct height (0.90m pelvis)
- [ ] Short training run (100 iters) completes successfully
- [ ] Rewards compute without NaN/Inf
- [ ] ONNX export works
- [ ] Cross-simulator evaluation tested (optional)
- [ ] Documentation updated (CLAUDE.md or README)

---

## References

- **G1 WBT Config:** `src/holosoma/holosoma/config_values/wbt/g1/`
- **Adam Pro Constants:** `src/holosoma/holosoma/data/robots/adam_pro/constants.py`
- **Adam Pro Robot Config:** `src/holosoma/holosoma/config_values/robot.py` (line 1094+)
- **Retargeted Motion Data:** `src/holosoma_retargeting/holosoma_retargeting/converted_res/robot_only/lafan1/dance1_subject1_mj_fps50.npz`
- **WBT Architecture:** `src/holosoma/holosoma/managers/command/terms/wbt.py` (1141 lines)

---

**End of Design Document**
