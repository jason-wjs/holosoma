# Adam Pro WBT Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Whole-Body Tracking (WBT) training support for Adam Pro (29-DoF) humanoid robot in IsaacSim simulator.

**Architecture:** Shadow G1's WBT configuration structure with robot-specific adjustments. Reuse existing `robot.adam_pro_29dof` config, create new WBT manager configs under `config_values/wbt/adam_pro/`, register experiment presets.

**Tech Stack:** Python 3.11+, Pydantic dataclasses, Tyro CLI, IsaacSim simulator, PPO/FastSAC RL algorithms

---

## Task 1: Create Directory Structure

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/`

**Step 1: Create directory**

```bash
mkdir -p src/holosoma/holosoma/config_values/wbt/adam_pro
```

Run: `ls -la src/holosoma/holosoma/config_values/wbt/`
Expected: Output shows `adam_pro/` directory listed

**Step 2: Verify directory created**

Run: `test -d src/holosoma/holosoma/config_values/wbt/adam_pro && echo "EXISTS"`
Expected: Output shows "EXISTS"

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/
git commit -m "feat: create adam_pro wbt config directory"
```

---

## Task 2: Create Action Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/action.py`

**Step 1: Write action config file**

```python
"""Whole Body Tracking action presets for Adam Pro robot."""

from holosoma.config_types.action import ActionManagerCfg, ActionTermCfg

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

__all__ = ["adam_pro_29dof_joint_pos"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/action.py`
Expected: No output (successful compilation)

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/action.py
git commit -m "feat: add adam pro wbt action config"
```

---

## Task 3: Create Command Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/command.py`

**Step 1: Write command config file**

```python
"""Whole Body Tracking command presets for Adam Pro robot."""

from dataclasses import replace

from holosoma.config_types.command import CommandManagerCfg, CommandTermCfg, MotionConfig, NoiseToInitialPoseConfig

init_pose_config = NoiseToInitialPoseConfig(
    overall_noise_scale=1.0,
    dof_pos=0.1,  # TODO: Tune for Adam Pro
    root_pos=[0.05, 0.05, 0.01],
    root_rot=[0.1, 0.1, 0.2],
    root_lin_vel=[0.1, 0.1, 0.05],
    root_ang_vel=[0.1, 0.1, 0.1],
    object_pos=[0.05, 0.05, 0.0],
)

motion_config = MotionConfig(
    motion_file="holosoma/data/motions/adam_pro_29dof/whole_body_tracking/dance1_subject1_mj_fps50.npz",
    body_names_to_track=[
        # Core bodies (from actual motion file)
        "pelvis",
        "torso_link",
        # Left leg (link names from motion file)
        "left_hip_pitch_link",
        "left_knee_link",
        "left_ankle_roll_link",
        # Right leg
        "right_hip_pitch_link",
        "right_knee_link",
        "right_ankle_roll_link",
        # Left arm
        "left_shoulder_pitch_link",
        "left_elbow_link",
        "left_wrist_yaw_link",
        # Right arm
        "right_shoulder_pitch_link",
        "right_elbow_link",
        "right_wrist_yaw_link",
    ],
    body_name_ref=["torso_link"],  # Reference body for relative pose computation
    use_adaptive_timesteps_sampler=True,  # Enable adaptive sampling
    noise_to_initial_pose=init_pose_config,
)

adam_pro_29dof_wbt_command = CommandManagerCfg(
    params={},
    setup_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
            params={
                "motion_config": motion_config,
            },
        ),
    },
    reset_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        ),
    },
    step_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_command"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/command.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/command.py
git commit -m "feat: add adam pro wbt command config with motion file"
```

---

## Task 4: Create Curriculum Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/curriculum.py`

**Step 1: Write curriculum config file**

```python
"""Whole Body Tracking curriculum presets for Adam Pro robot."""

from holosoma.config_types.curriculum import CurriculumManagerCfg, TermCfg

adam_pro_29dof_wbt_curriculum = CurriculumManagerCfg(
    terms={
        "adaptive_sampling": TermCfg(
            func="holosoma.managers.curriculum.terms.wbt:adaptive_timestep_sampling",
            params={
                "num_bins": 30,  # 1-second bins for 50fps motion (30 bins * 50fps = 1500 frames ≈ 30s)
                "kernel_std": 2.0,  # Smoothing for adaptive sampling distribution
            },
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_curriculum"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/curriculum.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/curriculum.py
git commit -m "feat: add adam pro wbt curriculum config"
```

---

## Task 5: Create Observation Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/observation.py`

**Step 1: Write observation config file**

```python
"""Whole Body Tracking observation presets for Adam Pro robot."""

from holosoma.config_types.observation import ObservationManagerCfg, ObsGroupCfg, ObsTermCfg

# Actor observations (what policy sees)
actor_obs_shared = ObsGroupCfg(
    concatenate=True,
    enable_noise=True,
    history_length=1,
    terms={
        "motion_command": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:motion_command",
            scale=1.0,
            noise=0.0,
        ),
        "motion_ref_ori_b": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:motion_ref_ori_b",
            scale=1.0,
            noise=0.05,
        ),
        "base_ang_vel": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:base_ang_vel",
            scale=1.0,
            noise=0.2,
        ),
        "dof_pos": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:dof_pos",
            scale=1.0,
            noise=0.01,
        ),
        "dof_vel": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:dof_vel",
            scale=1.0,
            noise=0.5,
        ),
        "actions": ObsTermCfg(
            func="holosoma.managers.observation.terms.wbt:actions",
            scale=1.0,
            noise=0.0,
        ),
    },
)

# Critic observations (privileged information: full body poses)
critic_obs_shared_terms = {
    "motion_command": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:motion_command",
        scale=1.0,
        noise=0.0,
    ),
    "motion_ref_pos_b": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:motion_ref_pos_b",
        scale=1.0,
        noise=0.25,
    ),
    "motion_ref_ori_b": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:motion_ref_ori_b",
        scale=1.0,
        noise=0.05,
    ),
    "robot_body_pos_b": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:robot_body_pos_b",
        scale=1.0,
        noise=0.0,
    ),
    "robot_body_ori_b": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:robot_body_ori_b",
        scale=1.0,
        noise=0.0,
    ),
    "base_lin_vel": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:base_lin_vel",
        scale=1.0,
        noise=0.0,
    ),
    "base_ang_vel": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:base_ang_vel",
        scale=1.0,
        noise=0.2,
    ),
    "dof_pos": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:dof_pos",
        scale=1.0,
        noise=0.01,
    ),
    "dof_vel": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:dof_vel",
        scale=1.0,
        noise=0.5,
    ),
    "actions": ObsTermCfg(
        func="holosoma.managers.observation.terms.wbt:actions",
        scale=1.0,
        noise=0.0,
    ),
}

adam_pro_29dof_wbt_observation = ObservationManagerCfg(
    groups={
        "actor_obs": actor_obs_shared,
        "critic_obs": ObsGroupCfg(
            concatenate=True,
            enable_noise=False,
            history_length=1,
            terms=critic_obs_shared_terms,
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_observation"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/observation.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/observation.py
git commit -m "feat: add adam pro wbt observation config"
```

---

## Task 6: Create Randomization Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/randomization.py`

**Step 1: Write randomization config file**

```python
"""Whole Body Tracking randomization presets for Adam Pro robot."""

from holosoma.config_types.randomization import RandomizationManagerCfg, RandomizationTermCfg

# === Setup Terms ===
robot_state_dr_at_setup = {
    "randomize_robot_rigid_body_material_startup": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:randomize_robot_rigid_body_material_startup",
        params={
            "static_friction_range": [0.3, 1.6],
            "dynamic_friction_range": [0.3, 1.2],
            "restitution_range": [0.0, 0.5],
        },
    ),
    "randomize_base_com_startup": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:randomize_base_com_startup",
        params={
            "base_com_range": {"x": [-0.025, 0.025], "y": [-0.05, 0.05], "z": [-0.05, 0.05]},
            "enabled": True,
        },
    ),
    "setup_dof_pos_bias": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:setup_dof_pos_bias",
        params={
            "dof_pos_bias_range": [-0.025, 0.025],
            "enabled": True,
        },
    ),
}

base_setup_terms = {
    "push_randomizer_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:PushRandomizerState",
        params={
            "push_interval_s": [1.0, 3.0],  # Moderate: push every 1-3 seconds
            "max_push_vel": [0.5, 0.5, 0.2, 0.52, 0.52, 0.78],  # Moderate pushes
            "enabled": True,
        },
    ),
    "actuator_randomizer_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:ActuatorRandomizerState",
        params={
            "kp_range": [0.9, 1.1],  # ±10% PD gain variation
            "kd_range": [0.9, 1.1],
            "rfi_lim_range": [1.0, 1.0],
            "enable_pd_gain": True,
            "enable_rfi_lim": False,
        },
    ),
    "setup_action_delay_buffers": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:setup_action_delay_buffers",
        params={
            "ctrl_delay_step_range": [0, 1],
            "enabled": False,  # WBT typically no control delay
        },
    ),
    **robot_state_dr_at_setup,
}

# === Reset Terms ===
base_reset_terms = {
    "push_randomizer_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:PushRandomizerState",
    ),
    "randomize_push_schedule": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:randomize_push_schedule",
    ),
    "actuator_randomizer_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:ActuatorRandomizerState",
    ),
    "randomize_dof_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:randomize_dof_state",
        params={
            "joint_pos_scale_range": [1.0, 1.0],  # No additional randomization
            "joint_vel_range": [0.0, 0.0],
            "joint_pos_bias_range": [-0.025, 0.025],  # Moderate bias
            "randomize_dof_pos_bias": True,
        },
    ),
}

# === Step Terms ===
base_step_terms = {
    "push_randomizer_state": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:PushRandomizerState",
    ),
    "apply_pushes": RandomizationTermCfg(
        func="holosoma.managers.randomization.terms.locomotion:apply_pushes",
    ),
}

adam_pro_29dof_wbt_randomization = RandomizationManagerCfg(
    setup_terms={**base_setup_terms},
    reset_terms={**base_reset_terms},
    step_terms={**base_step_terms},
)

__all__ = ["adam_pro_29dof_wbt_randomization"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/randomization.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/randomization.py
git commit -m "feat: add adam pro wbt randomization config"
```

---

## Task 7: Create Reward Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/reward.py`

**Step 1: Write reward config file**

```python
"""Whole Body Tracking reward presets for Adam Pro robot."""

from holosoma.config_types.reward import RewardManagerCfg, RewardTermCfg

adam_pro_29dof_wbt_reward = RewardManagerCfg(
    terms={
        # === Global Reference Tracking ===
        "motion_global_ref_position": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_ref_position_error_exp",
            params={
                "sigma": 0.3,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        "motion_global_ref_orientation": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_ref_orientation_error_exp",
            params={
                "sigma": 0.4,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        # === Relative Body Tracking ===
        "motion_relative_body_position": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_relative_body_position_error_exp",
            params={
                "sigma": 0.3,  # TODO: Tune for Adam Pro dynamics
            },
            weight=2.0,
        ),
        "motion_relative_body_orientation": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_relative_body_orientation_error_exp",
            params={
                "sigma": 0.4,  # TODO: Tune for Adam Pro dynamics
            },
            weight=2.0,
        ),
        # === Body Velocities ===
        "motion_global_body_lin_vel": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_body_lin_vel",
            params={
                "sigma": 1.0,  # TODO: Tune for Adam Pro dynamics
            },
            weight=1.0,
        ),
        "motion_global_body_ang_vel": RewardTermCfg(
            func="holosoma.managers.reward.terms.wbt:motion_global_body_ang_vel",
            params={
                "sigma": 3.14,  # TODO: Tune for Adam Pro dynamics
            },
            weight=0.5,
        ),
        # === Regularization ===
        "penalty_action_rate": RewardTermCfg(
            func="holosoma.managers.reward.terms.common:penalty_action_rate",
            params={},
            weight=-0.1,  # PPO standard
        ),
        "limits_dof_pos": RewardTermCfg(
            func="holosoma.managers.reward.terms.common:limits_dof_pos",
            params={
                "tolerance": 0.01,  # TODO: Adjust for Adam Pro joint limits
            },
            weight=-100.0,
        ),
        "undesired_contacts": RewardTermCfg(
            func="holosoma.managers.reward.terms.common:undesired_contacts",
            params={
                "filter_params": {
                    "max_force": 1.0,  # TODO: Tune for Adam Pro contact parameters
                },
            },
            weight=-0.5,
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_reward"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/reward.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/reward.py
git commit -m "feat: add adam pro wbt reward config with todo thresholds"
```

---

## Task 8: Create Termination Configuration

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/termination.py`

**Step 1: Write termination config file**

```python
"""Whole Body Tracking termination presets for Adam Pro robot."""

from holosoma.config_types.termination import TerminationManagerCfg, TermCfg

adam_pro_29dof_wbt_termination = TerminationManagerCfg(
    terms={
        "bad_ref_tracking": TermCfg(
            func="holosoma.managers.termination.terms.wbt:bad_ref_tracking",
            params={
                "ref_pos_error_threshold": 0.5,  # TODO: Tune for Adam Pro (meters)
                "ref_ori_error_threshold": 1.0,  # TODO: Tune for Adam Pro (radians)
                "velocity_error_threshold": 2.0,  # TODO: Tune for Adam Pro (m/s)
            },
        ),
        "bad_joint_pos_limits": TermCfg(
            func="holosoma.managers.termination.terms.common:bad_joint_pos_limits",
            params={
                "clip_limit_to_violation_ratio": 0.98,  # TODO: Adjust for Adam Pro
            },
        ),
        "bad_contact": TermCfg(
            func="holosoma.managers.termination.terms.common:bad_contact",
            params={
                "max_undesired_contact_force": 200.0,  # TODO: Tune for Adam Pro (Newtons)
                "max_contact_duration": 0.1,  # seconds
            },
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_termination"]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/termination.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/termination.py
git commit -m "feat: add adam pro wbt termination config with todo thresholds"
```

---

## Task 9: Create Experiment Presets

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/experiment.py`

**Step 1: Write experiment config file**

```python
"""Whole Body Tracking experiment presets for Adam Pro robot."""

from dataclasses import replace

from holosoma.config_types.experiment import ExperimentConfig, NightlyConfig, TrainingConfig
from holosoma.config_values import (
    action,
    algo,
    command,
    curriculum,
    observation,
    randomization,
    reward,
    robot,
    simulator,
    termination,
    terrain,
)

# PPO variant
adam_pro_29dof_wbt = ExperimentConfig(
    env_class="holosoma.envs.wbt.wbt_manager.WholeBodyTrackingManager",
    training=TrainingConfig(
        project="WholeBodyTracking",
        name="adam_pro_29dof_wbt",
        num_envs=8192,
    ),
    algo=replace(
        algo.ppo,
        config=replace(
            algo.ppo.config,
            num_learning_iterations=40000,  # TODO: Tune based on motion length
            save_interval=4000,
            entropy_coef=0.005,
            init_noise_std=1.0,
            init_at_random_ep_len=False,
            use_symmetry=False,  # WBT doesn't use symmetry
            actor_optimizer=replace(algo.ppo.config.actor_optimizer, weight_decay=0.000),
            critic_optimizer=replace(algo.ppo.config.critic_optimizer, weight_decay=0.000),
        ),
    ),
    simulator=replace(
        simulator.isaacsim,
        config=replace(
            simulator.isaacsim.config,
            sim=replace(
                simulator.isaacsim.config.sim,
                max_episode_length_s=10.0,  # TODO: Adjust to motion clip length
            ),
        ),
    ),
    robot=replace(
        robot.adam_pro_29dof,  # REUSE EXISTING ROBOT CONFIG
        control=replace(robot.adam_pro_29dof.control, action_scale=1.0),  # WBT uses 1.0
        asset=replace(robot.adam_pro_29dof.asset, enable_self_collisions=True),
        init_state=replace(
            robot.adam_pro_29dof.init_state,
            pos=[0.0, 0.0, 0.90],  # ADAM PRO PELVIS HEIGHT (not 0.76m like G1)
        ),
    ),
    terrain=terrain.terrain_locomotion_plane,  # Flat terrain for WBT
    observation=observation.adam_pro_29dof_wbt_observation,
    action=action.adam_pro_29dof_joint_pos,
    command=command.adam_pro_29dof_wbt_command,
    reward=reward.adam_pro_29dof_wbt_reward,
    termination=termination.adam_pro_29dof_wbt_termination,
    randomization=randomization.adam_pro_29dof_wbt_randomization,
    curriculum=curriculum.adam_pro_29dof_wbt_curriculum,
)

# FastSAC variant
adam_pro_29dof_wbt_fast_sac = ExperimentConfig(
    env_class="holosoma.envs.wbt.wbt_manager.WholeBodyTrackingManager",
    training=TrainingConfig(
        project="WholeBodyTracking",
        name="adam_pro_29dof_wbt_fast_sac",
        num_envs=8192,
    ),
    algo=replace(
        algo.fast_sac,
        config=replace(
            algo.fast_sac.config,
            num_learning_iterations=400000,
            v_max=20.0,
            v_min=-20.0,
            gamma=0.99,  # For motion tracking, high gamma + high num_steps is better
            num_steps=1,
            num_updates=4,
            num_atoms=501,
            policy_frequency=2,
            target_entropy_ratio=0.5,
            tau=0.05,
            use_symmetry=False,
        ),
    ),
    simulator=replace(
        simulator.isaacsim,
        config=replace(
            simulator.isaacsim.config,
            sim=replace(
                simulator.isaacsim.config.sim,
                max_episode_length_s=10.0,
            ),
        ),
    ),
    robot=replace(
        robot.adam_pro_29dof,
        control=replace(robot.adam_pro_29dof.control, action_scale=1.0),
        asset=replace(robot.adam_pro_29dof.asset, enable_self_collisions=True),
        init_state=replace(
            robot.adam_pro_29dof.init_state,
            pos=[0.0, 0.0, 0.90],
        ),
    ),
    terrain=terrain.terrain_locomotion_plane,
    observation=observation.adam_pro_29dof_wbt_observation,
    action=action.adam_pro_29dof_joint_pos,
    command=command.adam_pro_29dof_wbt_command,
    reward=reward.adam_pro_29dof_wbt_reward,
    termination=termination.adam_pro_29dof_wbt_termination,
    randomization=randomization.adam_pro_29dof_wbt_randomization,
    curriculum=curriculum.adam_pro_29dof_wbt_curriculum,
)

__all__ = [
    "adam_pro_29dof_wbt",
    "adam_pro_29dof_wbt_fast_sac",
]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/experiment.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/experiment.py
git commit -m "feat: add adam pro wbt experiment presets (ppo and fastsac)"
```

---

## Task 10: Create __init__.py Package Export

**Files:**
- Create: `src/holosoma/holosoma/config_values/wbt/adam_pro/__init__.py`

**Step 1: Write __init__.py file**

```python
"""Whole Body Tracking config presets for Adam Pro robot."""

from holosoma.config_types.experiment import ExperimentConfig
from holosoma.config_values.wbt.adam_pro.experiment import (
    adam_pro_29dof_wbt,
    adam_pro_29dof_wbt_fast_sac,
)
from holosoma.config_values.wbt.adam_pro.action import adam_pro_29dof_joint_pos
from holosoma.config_values.wbt.adam_pro.command import adam_pro_29dof_wbt_command
from holosoma.config_values.wbt.adam_pro.curriculum import adam_pro_29dof_wbt_curriculum
from holosoma.config_values.wbt.adam_pro.observation import adam_pro_29dof_wbt_observation
from holosoma.config_values.wbt.adam_pro.randomization import adam_pro_29dof_wbt_randomization
from holosoma.config_values.wbt.adam_pro.reward import adam_pro_29dof_wbt_reward
from holosoma.config_values.wbt.adam_pro.termination import adam_pro_29dof_wbt_termination

__all__ = [
    "adam_pro_29dof_wbt",
    "adam_pro_29dof_wbt_fast_sac",
    "adam_pro_29dof_joint_pos",
    "adam_pro_29dof_wbt_command",
    "adam_pro_29dof_wbt_curriculum",
    "adam_pro_29dof_wbt_observation",
    "adam_pro_29dof_wbt_randomization",
    "adam_pro_29dof_wbt_reward",
    "adam_pro_29dof_wbt_termination",
]
```

**Step 2: Verify file syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/wbt/adam_pro/__init__.py`
Expected: No output

**Step 3: Commit**

```bash
git add src/holosoma/holosoma/config_values/wbt/adam_pro/__init__.py
git commit -m "feat: add adam pro wbt config package exports"
```

---

## Task 11: Register Experiment Presets

**Files:**
- Modify: `src/holosoma/holosoma/config_values/experiment.py:15-26`

**Step 1: Read existing experiment.py imports**

Run: `head -30 src/holosoma/holosoma/config_values/experiment.py`
Expected: Output shows import structure

**Step 2: Add adam_pro imports to experiment.py**

Add at top of file after line 7 (after g1 imports):

```python
from holosoma.config_values.wbt.adam_pro.experiment import (
    adam_pro_29dof_wbt,
    adam_pro_29dof_wbt_fast_sac,
)
```

**Step 3: Register in DEFAULTS dict**

Add to DEFAULTS dict (around line 16):

```python
DEFAULTS = {
    # ... existing entries ...
    "adam_pro_29dof_wbt": adam_pro_29dof_wbt,
    "adam_pro_29dof_wbt_fast_sac": adam_pro_29dof_wbt_fast_sac,
}
```

**Step 4: Verify syntax**

Run: `python3 -m py_compile src/holosoma/holosoma/config_values/experiment.py`
Expected: No output

**Step 5: Test CLI help shows new presets**

Run: `python src/holosoma/holosoma/train_agent.py --help | grep adam-pro`
Expected: Output shows `exp:adam-pro-29dof-wbt` and `exp:adam-pro-29dof-wbt-fast-sac`

**Step 6: Commit**

```bash
git add src/holosoma/holosoma/config_values/experiment.py
git commit -m "feat: register adam pro wbt experiment presets"
```

---

## Task 12: Dry Run Test

**Files:**
- Test: None (integration test)

**Step 1: Run dry run with 1 iteration**

```bash
cd /mnt/data/Junsong_WU/ADAM/holosoma
source scripts/source_isaacsim_setup.sh 2>/dev/null || true
python src/holosoma/holosoma/train_agent.py \
    exp:adam-pro-29dof-wbt \
    simulator:isaacsim \
    --training.num_learning_iterations 1 \
    --training.num_envs 256
```

Expected output:
- Environment initializes without errors
- Motion file loads successfully
- Robot spawns at correct height (0.90m)
- Training loop completes 1 iteration
- Exit code: 0

**Step 2: Check for errors in output**

If errors occur:
1. Check motion file path is correct
2. Verify body names match motion file
3. Confirm `robot.adam_pro_29dof` config exists
4. Check IsaacSim is installed and licensed

**Step 3: Commit successful test**

```bash
git add -A
git commit -m "test: verify adam pro wbt dry run succeeds"
```

---

## Task 13: Short Training Run

**Files:**
- Test: None (integration test)

**Step 1: Run short training (100 iterations)**

```bash
cd /mnt/data/Junsong_WU/ADAM/holosoma
source scripts/source_isaacsim_setup.sh 2>/dev/null || true
python src/holosoma/holosoma/train_agent.py \
    exp:adam-pro-29dof-wbt \
    simulator:isaacsim \
    --training.num_learning_iterations 100 \
    --training.num_envs 1024 \
    --logger=wandb \
    --training.project "adam-pro-wbt-test" \
    --training.name "short-run-test"
```

Expected output:
- Episodes complete successfully
- Rewards compute (check tracking metrics logged)
- No NaN/Inf in observations or rewards
- ONNX export works at checkpoint
- WandB logging works (if API key configured)

**Step 2: Monitor key metrics**

Check WandB or console output for:
- `Episode/rew_motion_global_ref_position_error_exp` - should be > 0
- `Episode/rew_motion_global_ref_orientation_error_exp` - should be > 0
- `Episode/rew_motion_relative_body_position_error_exp` - should be > 0
- `Episode/rew_motion_relative_body_orientation_error_exp` - should be > 0

**Step 3: Verify checkpoint created**

Run: `ls -la ~/holosoma_logs/adam-pro-wbt-test/`
Expected: Output shows checkpoint directories and model.onnx file

**Step 4: Commit successful test**

```bash
git add -A
git commit -m "test: verify adam pro wbt short training run succeeds"
```

---

## Task 14: Update Documentation

**Files:**
- Modify: `CLAUDE.md:186-220`

**Step 1: Read existing robot support section**

Run: `grep -A 35 "Robot support:" CLAUDE.md | head -40`
Expected: Shows current robot support documentation

**Step 2: Add Adam Pro WBT entry**

After "Booster T1, and Adam Pro humanoids" line, add:

```markdown
- **Adam Pro** (locomotion: MJWarp; WBT: IsaacSim)
```

In experiment presets section, add:

```markdown
**Whole-Body Tracking (Adam Pro):**
- `exp:adam-pro-29dof-wbt` - Adam Pro WBT with PPO
- `exp:adam-pro-29dof-wbt-fast-sac` - Adam Pro WBT with FastSAC
```

**Step 3: Verify markdown format**

Run: `grep -c "adam-pro" CLAUDE.md`
Expected: Output shows count >= 2

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add adam pro wbt support to CLAUDE.md"
```

---

## Task 15: Final Validation

**Files:**
- Test: None (validation)

**Step 1: Verify all files exist**

Run: `ls -1 src/holosoma/holosoma/config_values/wbt/adam_pro/*.py`
Expected: Output lists all 9 files (action.py, command.py, curriculum.py, experiment.py, observation.py, randomization.py, reward.py, termination.py, __init__.py)

**Step 2: Verify imports work**

```bash
cd /mnt/data/Junsong_WU/ADAM/holosoma
python3 -c "
from holosoma.config_values import experiment
print('Available adam_pro presets:')
for k in experiment.DEFAULTS.keys():
    if 'adam_pro' in k:
        print(f'  - {k}')
"
```

Expected output:
```
Available adam_pro presets:
 - adam_pro_29dof_wbt
 - adam_pro_29dof_wbt_fast_sac
```

**Step 3: Verify config loads without errors**

```bash
python3 -c "
import tyro
from holosoma.config_values.experiment import AnnotatedExperimentConfig, DEFAULTS

# Try to load adam_pro config
config = DEFAULTS['adam_pro_29dof_wbt']
print(f'Config loaded: {config.training.name}')
print(f'Env class: {config.env_class}')
print(f'Simulator: {config.simulator.config.__class__.__name__}')
print(f'Robot DOF: {config.robot.dof_obs_size}')
"
```

Expected output:
```
Config loaded: adam_pro_29dof_wbt
Env class: holosoma.envs.wbt.wbt_manager.WholeBodyTrackingManager
Simulator: IsaacSimConfig
Robot DOF: 29
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete adam pro wbt support implementation"
```

---

## Summary

**Total Tasks:** 15
**Estimated Time:** 45-75 minutes
**Files Created:** 9 new config files
**Files Modified:** 2 (experiment.py, CLAUDE.md)
**Total Lines:** ~609 lines of config code

**Key Acceptance Criteria:**
- [x] All config files created and syntactically valid
- [x] Experiment presets registered in DEFAULTS
- [x] CLI help shows new presets
- [x] Dry run completes without errors
- [x] Short training run (100 iters) succeeds
- [x] ONNX export works
- [x] Documentation updated

**Post-Implementation TODOs:**
1. Tune reward sigma values based on actual training performance
2. Adjust termination thresholds for Adam Pro dynamics
3. Verify adaptive sampling works (check hard samples prioritized)
4. Add additional motion file presets as needed
5. Extend to object interaction (optional)
6. Add IsaacSim locomotion support (optional)

**References:**
- Design document: `docs/plans/2026-02-14-adam-pro-wbt-support-design.md`
- G1 WBT configs: `src/holosoma/holosoma/config_values/wbt/g1/`
- Adam Pro robot config: `src/holosoma/holosoma/config_values/robot.py:1094-1675`
- Motion data: `src/holosoma_retargeting/holosoma_retargeting/converted_res/robot_only/lafan1/dance1_subject1_mj_fps50.npz`
