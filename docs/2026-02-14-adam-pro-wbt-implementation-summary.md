# Adam Pro WBT Support Implementation - Summary

**Date:** 2026-02-14  
**Status:** In progress (code wiring fixed, runtime environment still partially broken)

## Implemented

- Adam Pro WBT config package exists under `src/holosoma/holosoma/config_values/wbt/adam_pro/`.
- Experiment presets are registered:
  - `exp:adam-pro-29dof-wbt`
  - `exp:adam-pro-29dof-wbt-fast-sac`
- Adam Pro WBT is now fully wired through top-level config registries:
  - `src/holosoma/holosoma/config_values/command.py`
  - `src/holosoma/holosoma/config_values/reward.py`
  - `src/holosoma/holosoma/config_values/randomization.py`
  - `src/holosoma/holosoma/config_values/termination.py`
  - `src/holosoma/holosoma/config_values/curriculum.py`
- `CLAUDE.md` preset docs were corrected to 29-DoF names (removed stale `30dof`/`w-object` Adam Pro entries).

## Fixes Added During Reanalysis

1. Fixed Adam Pro WBT simulator config shape in
   `src/holosoma/holosoma/config_values/wbt/adam_pro/experiment.py`
   to keep `SimulatorInitConfig` (matching G1 pattern).
2. Fixed Adam Pro observation registration path:
   `src/holosoma/holosoma/config_values/observation.py`.
3. Removed circular-import behavior from
   `src/holosoma/holosoma/config_values/wbt/adam_pro/__init__.py`.
4. Updated Adam Pro WBT curriculum/termination to use current framework config types and valid term APIs:
   - `src/holosoma/holosoma/config_values/wbt/adam_pro/curriculum.py`
   - `src/holosoma/holosoma/config_values/wbt/adam_pro/termination.py`
5. Added regression coverage file:
   `src/holosoma/tests/config_values/test_adam_pro_wbt_config.py`.

## Verification Evidence

- `python3 -m py_compile ...` passed for all edited config files.
- Config load check passed:
  - `DEFAULTS['adam_pro_29dof_wbt']` and `DEFAULTS['adam_pro_29dof_wbt_fast_sac']` exist.
  - Both now hold `SimulatorInitConfig`.
- CLI help shows both new presets when dependencies are made visible via `PYTHONPATH`.

## Remaining Blockers

### 1) IsaacSim environment reconstruction is incomplete

After `source scripts/source_isaacsim_setup.sh`, `hssim` is missing several expected Python deps (`tyro`, `loguru`, etc.).  
Root cause appears to be a stale setup sentinel at:

- `~/.holosoma_deps/.env_setup_finished_hssim`

while package installation did not complete successfully for this laptop.

### 2) Dry run still blocked by IsaacLab/IsaacSim environment mismatch

A 1-iteration dry run was attempted with motion-file override:

- `/home/humanoid/wjs/Adam/holosoma/src/holosoma_retargeting/holosoma_retargeting/converted_res/robot_only/lafan1/dance1_subject1_mj_fps50.npz`

Current blocker is runtime environment incompatibility (not Adam Pro WBT config wiring), including:

- missing `gymnasium`
- `isaaclab` + IsaacSim API mismatch:
  `omni.physx.bindings._physx` missing `SETTING_BACKWARD_COMPATIBILITY`

## Practical Next Steps

1. Rebuild `hssim` dependencies cleanly (or re-run `scripts/setup_isaacsim.sh` after clearing stale sentinel).
2. Ensure IsaacLab version matches installed IsaacSim runtime for this machine.
3. Re-run:
   - `python src/holosoma/holosoma/train_agent.py --help`
   - 1-iteration Adam Pro WBT dry run in IsaacSim.

Once environment is corrected, the Adam Pro WBT config path itself is ready for runtime validation.
