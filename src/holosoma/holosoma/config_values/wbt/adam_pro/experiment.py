"""Whole Body Tracking experiment presets for Adam Pro robot."""

from dataclasses import replace

from holosoma.config_types.experiment import ExperimentConfig, TrainingConfig
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
