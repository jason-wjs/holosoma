# Adam Pro WBT Support Implementation - Summary

**Date:** 2026-02-15  
**Status:** Runtime-validated in IsaacSim (1-iteration dry run passes)

## What Is Implemented

- Adam Pro WBT config package exists under `src/holosoma/holosoma/config_values/wbt/adam_pro/`.
- Experiment presets are registered and visible in CLI:
  - `exp:adam-pro-29dof-wbt`
  - `exp:adam-pro-29dof-wbt-fast-sac`
- Adam Pro WBT remains wired through top-level registries:
  - `src/holosoma/holosoma/config_values/command.py`
  - `src/holosoma/holosoma/config_values/reward.py`
  - `src/holosoma/holosoma/config_values/randomization.py`
  - `src/holosoma/holosoma/config_values/termination.py`
  - `src/holosoma/holosoma/config_values/curriculum.py`

## Reanalysis Fixes Added

1. IsaacSim setup/runtime fixes:
   - `scripts/setup_isaacsim.sh` now re-validates stale sentinel state, validates IsaacLab ref, uses valid `isaaclab.sh --install` framework syntax, and aligns `wandb` with holosoma pin.
2. Updated Adam Pro URDF for true 29-DOF IsaacSim actuation:
   - `src/holosoma/holosoma/data/robots/adam_pro/adam_pro.urdf`
   - Wrist joints (`wristYaw/Pitch/Roll` on both arms) are now revolute with limits.
   - Added `left_foot_contact_point` and `right_foot_contact_point` fixed links for parity with existing robot config body names.
3. Switched Adam Pro WBT experiments back to pure 29-DOF robot profile:
   - `src/holosoma/holosoma/config_values/wbt/adam_pro/experiment.py`
4. Fixed Adam Pro WBT reward wiring to current term APIs:
   - `src/holosoma/holosoma/config_values/wbt/adam_pro/reward.py`
5. Fixed Adam Pro WBT termination params for current `BadTracking` contract:
   - `src/holosoma/holosoma/config_values/wbt/adam_pro/termination.py`
6. Added Adam Pro motion name aliasing for IsaacSim body/joint naming mismatch:
   - `src/holosoma/holosoma/managers/command/terms/wbt.py`
7. Expanded regression tests:
   - `src/holosoma/tests/config_values/test_adam_pro_wbt_config.py`

## Verification Evidence

- `pytest -q src/holosoma/tests/config_values/test_adam_pro_wbt_config.py` passes (`5 passed`).
- 1-iteration IsaacSim dry run succeeds with motion override:
  - `python src/holosoma/holosoma/train_agent.py exp:adam-pro-29dof-wbt simulator:isaacsim --algo.config.num-learning-iterations 1 --training.num-envs 16 --logger.video.enabled False --command.setup-terms.motion-command.params.motion-config.motion-file /home/humanoid/wjs/Adam/holosoma/src/holosoma_retargeting/holosoma_retargeting/converted_res/robot_only/lafan1/dance1_subject1_mj_fps50.npz`
  - Checkpoint/log output observed at:
    - `logs/WholeBodyTracking/20260214_163122-adam_pro_29dof_wbt-locomotion/`
  - Training metrics printed and process exits cleanly.

## Notes

- Preset names and runtime now both use true Adam Pro 29-DOF in IsaacSim.

## Remaining Work

1. Run short stability training (e.g., 100 iterations) and inspect reward/termination behavior.
2. Optionally add explicit docs note in `CLAUDE.md` that Adam Pro IsaacSim now matches MJCF wrist actuation (29-DOF).
