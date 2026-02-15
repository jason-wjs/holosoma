# MJLAB Backend Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate `mjlab v1.1.1` as a new `BaseSimulator` backend in holosoma with intentional target-based actuator semantics and phase-1 G1 locomotion support on flat terrain.

**Architecture:** Add a new `holosoma.simulator.mjlab` backend that maps holosoma robot/config abstractions to MJLab `Scene/Entity/Simulation`, with explicit state adapters and deterministic step/refresh sequencing. Preserve compatibility by keeping `apply_torques_at_dof()` implemented for bridge callers, while the primary training path uses simulator-owned target buffers consumed during the physics step.

**Tech Stack:** Python, PyTorch, MuJoCo/MJLab APIs, Tyro config system, pytest

---

## Locked Decisions

- Bridge precedence: when bridge is enabled and provides effort commands, bridge effort commands override target buffers for that step.
- Contact forces source: phase-1 `contact_forces` tensor is populated from MJLAB contact sensor outputs (public API path).
- Environment setup: `scripts/setup_mjlab.sh` is strict package mode with pinned `mjlab==1.1.1` only; fail fast if unavailable.
- Dependency policy for `hsmjlab`: allow MJLAB-required versions to win (Torch/Warp/W&B). Install holosoma editable in no-deps mode in this env to avoid hard pin conflicts with MJLAB requirements.

---

## Task 1: Add Isolated MJLAB Setup Script (`hsmjlab`, Pinned Release)

**Files:**
- Create: `scripts/setup_mjlab.sh`
- Modify: `src/holosoma/README.md`

**Step 1: Write failing setup contract**

Define script acceptance criteria in comments at the top of `scripts/setup_mjlab.sh`:
- Creates/updates `hsmjlab` conda environment by default
- Uses Python `3.11` by default
- Installs holosoma editable package in no-deps mode
- Installs pinned `mjlab==1.1.1` (no local-source mode)
- Verifies `import mjlab` and prints version
- Verifies `import holosoma` succeeds in the same environment

Expected failure before implementation: `bash scripts/setup_mjlab.sh --help` returns non-zero (file missing).

**Step 2: Implement minimal setup script**

Add a non-interactive script with:
- `set -euo pipefail`
- `--env-name` (default `hsmjlab`)
- `--python` (default `3.11`)
- `--force-recreate` optional flag
- install sequence with pinned `mjlab==1.1.1`
- install order: `pip install mjlab==1.1.1` then `pip install -e src/holosoma --no-deps`

**Step 3: Add usage docs**

Document setup and activation flow in `src/holosoma/README.md` under a new MJLAB section.

**Step 4: Verify script syntax and help**

Run: `bash -n scripts/setup_mjlab.sh`
Expected: no output

Run: `bash scripts/setup_mjlab.sh --help`
Expected: usage text printed, exit code `0`

**Step 5: Commit**

```bash
git add scripts/setup_mjlab.sh src/holosoma/README.md
git commit -m "build: add pinned mjlab setup workflow for hsmjlab env"
```

---

## Task 2: Register Simulator Type and Config Preset

**Files:**
- Modify: `src/holosoma/holosoma/utils/simulator_config.py`
- Modify: `src/holosoma/holosoma/config_values/simulator.py`
- Test: `src/holosoma/tests/config_values/test_mjlab_simulator_config.py`

**Step 1: Write failing tests**

Add `test_mjlab_simulator_config.py` to assert:
- `SimulatorType` includes `MJLAB`
- `config_values.simulator.DEFAULTS["mjlab"]` exists
- `_target_` and `config.name` stay consistent

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_simulator_config.py -v`
Expected: FAIL because MJLAB type/default not present.

**Step 2: Implement config/type registration**

Add:
- `SimulatorType.MJLAB = "mjlab"`
- new `simulator:mjlab` default preset targeting `holosoma.simulator.mjlab.mjlab_simulator.MJLab`

**Step 3: Re-run test**

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_simulator_config.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/utils/simulator_config.py src/holosoma/holosoma/config_values/simulator.py src/holosoma/tests/config_values/test_mjlab_simulator_config.py
git commit -m "feat: register mjlab simulator type and config preset"
```

---

## Task 3: Create MJLAB Backend Package Skeleton and Adapters

**Files:**
- Create: `src/holosoma/holosoma/simulator/mjlab/__init__.py`
- Create: `src/holosoma/holosoma/simulator/mjlab/entity_adapter.py`
- Create: `src/holosoma/holosoma/simulator/mjlab/state_adapter.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_entity_adapter.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_state_adapter.py`

**Step 1: Write failing adapter tests**

`test_entity_adapter.py`:
- robot config to `EntityCfg` conversion
- resolves `@holosoma/...` asset root at runtime
- initial state mapping correctness

`test_state_adapter.py`:
- `wxyz <-> xyzw` quaternion roundtrip
- root state pack/unpack shape `[N, 13]`

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_entity_adapter.py src/holosoma/tests/simulators/mjlab/test_state_adapter.py -v`
Expected: FAIL due to missing module/functions.

**Step 2: Implement adapters**

Implement `entity_adapter.py`:
- Robot config to MJLab `EntityCfg`
- actuator config hooks for target-based control
- asset path normalization for `@holosoma` prefix

Implement `state_adapter.py`:
- root-state conversions between holosoma and MJLab conventions
- helper functions for batched tensor conversion

**Step 3: Re-run adapter tests**

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_entity_adapter.py src/holosoma/tests/simulators/mjlab/test_state_adapter.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/simulator/mjlab/__init__.py src/holosoma/holosoma/simulator/mjlab/entity_adapter.py src/holosoma/holosoma/simulator/mjlab/state_adapter.py src/holosoma/tests/simulators/mjlab/test_entity_adapter.py src/holosoma/tests/simulators/mjlab/test_state_adapter.py
git commit -m "feat: add mjlab adapters for entity and state mapping"
```

---

## Task 4: Implement Target-Based Action Semantics With Compatibility Path

**Files:**
- Create: `src/holosoma/holosoma/managers/action/terms/joint_control_mjlab.py`
- Modify: `src/holosoma/holosoma/config_values/loco/g1/action.py`
- Modify: `src/holosoma/holosoma/config_values/action.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_joint_control_mjlab.py`

**Step 1: Write failing control-semantics tests**

Add tests for MJLAB action behavior:
- control type `P` writes position targets into simulator-owned buffers
- control type `V` writes velocity targets into simulator-owned buffers
- control type `T` writes effort targets into simulator-owned buffers
- action term does not directly call low-level MJLAB entity APIs
- actuator randomization hooks still apply (`attach_actuator_scales`, `configure_torque_rfi`)

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_joint_control_mjlab.py -v`
Expected: FAIL due to missing MJLAB action term and buffer plumbing.

**Step 2: Implement MJLAB action term and buffers**

Create `JointTargetActionTermMJLab` that:
- inherits `JointPositionActionTerm` to preserve existing randomization `isinstance(...)` contracts
- processes actions similarly to existing joint control term
- writes targets into simulator-owned buffers (not direct low-level writes)
- preserves manager interfaces used by reward/termination logging

**Step 3: Wire config defaults**

Add an MJLAB-specific G1 locomotion action preset using the new term and register in `config_values/action.py`.

**Step 4: Re-run tests**

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_joint_control_mjlab.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/holosoma/holosoma/managers/action/terms/joint_control_mjlab.py src/holosoma/holosoma/config_values/loco/g1/action.py src/holosoma/holosoma/config_values/action.py src/holosoma/tests/simulators/mjlab/test_joint_control_mjlab.py
git commit -m "feat: add mjlab target-action path with bridge-compatible torque API"
```

---

## Task 5: Implement MJLAB Simulator Core and Step/Refresh Sequencing

**Files:**
- Create: `src/holosoma/holosoma/simulator/mjlab/mjlab_simulator.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_mjlab_interface_contract.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_mjlab_step_sequence.py`

**Step 1: Write failing interface and sequencing tests**

Add tests asserting MJLAB simulator:
- implements lifecycle: `setup`, `load_assets`, `create_envs`, `prepare_sim`, `refresh_sim_tensors`
- populates runtime tensors: `dof_state`, `dof_pos`, `dof_vel`, `robot_root_states`, `all_root_states`, `contact_forces`
- provides APIs used by locomotion: `set_actor_root_state_tensor_robots`, `set_dof_state_tensor_robots`, `find_rigid_body_indice`, `clear_contact_forces_history`, `time`
- enforces step order: apply target buffers -> write scene data -> `sim.step()` -> `scene.update()` -> forward freshness before derived-state reads
- keeps `apply_torques_at_dof()` callable for bridge path and defines bridge-over-target precedence for mixed-control steps

Run:
`python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_interface_contract.py src/holosoma/tests/simulators/mjlab/test_mjlab_step_sequence.py -v`
Expected: FAIL because backend implementation is missing/incomplete.

**Step 2: Implement simulator class**

Implement `MJLab(BaseSimulator)` with:
- `SceneCfg/EntityCfg` construction and model compile
- environment creation and tensor initialization
- simulator-owned target buffers and write/reset policies
- object registry registration for robot
- actor/root/dof read-write methods and format conversions
- deterministic `simulate_at_each_physics_step()` sequencing and `refresh_sim_tensors()` forward policy
- bridge compatibility path via `apply_torques_at_dof()`

**Step 3: Re-run tests**

Run:
`python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_interface_contract.py src/holosoma/tests/simulators/mjlab/test_mjlab_step_sequence.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/simulator/mjlab/mjlab_simulator.py src/holosoma/tests/simulators/mjlab/test_mjlab_interface_contract.py src/holosoma/tests/simulators/mjlab/test_mjlab_step_sequence.py
git commit -m "feat: implement mjlab simulator core with deterministic step sequencing"
```

---

## Task 6: Implement Contact-Force and Body-Index Mapping for Phase 1

**Files:**
- Modify: `src/holosoma/holosoma/simulator/mjlab/mjlab_simulator.py`
- Test: `src/holosoma/tests/simulators/mjlab/test_mjlab_contact_forces.py`

**Step 1: Write failing contact-force tests**

Add tests to validate phase-1 requirements used by G1 reward/termination:
- `find_rigid_body_indice()` returns stable indices aligned with simulator tensors
- `contact_forces[:, body_idx, :]` is populated and finite after stepping/contact
- contact history clear/reset semantics are correct

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_contact_forces.py -v`
Expected: FAIL before mapping is implemented.

**Step 2: Implement mapping**

Implement body index mapping and contact-force extraction path for MJLAB backend from contact sensor outputs (phase-1 sufficient for locomotion terms):
- create/configure contact sensor(s) through MJLAB public sensor API in scene setup
- build `body_name -> index` and ensure `find_rigid_body_indice()` uses the same index space as `contact_forces` and rigid-body tensors
- keep deterministic ordering by constructing contact-force slots from resolved body names and storing explicit mapping

**Step 3: Re-run tests**

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_contact_forces.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/simulator/mjlab/mjlab_simulator.py src/holosoma/tests/simulators/mjlab/test_mjlab_contact_forces.py
git commit -m "feat: add mjlab contact-force and body-index mapping for locomotion"
```

---

## Task 7: Add MJLAB-Safe Randomization Preset (Disable Unsupported Terms)

**Files:**
- Modify: `src/holosoma/holosoma/config_values/loco/g1/randomization.py`
- Modify: `src/holosoma/holosoma/config_values/randomization.py`
- Test: `src/holosoma/tests/config_values/test_mjlab_randomization_config.py`

**Step 1: Write failing randomization config tests**

Add tests verifying the MJLAB preset excludes unsupported startup terms:
- no mass startup randomization term (`mass_randomizer` / `randomize_mass_startup`)
- no `randomize_friction_startup`
- no `randomize_base_com_startup`

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_randomization_config.py -v`
Expected: FAIL before preset exists.

**Step 2: Implement preset**

Add `g1_29dof_randomization_mjlab` in `loco/g1/randomization.py` by copying base preset and removing unsupported startup terms.

Register default key in `config_values/randomization.py`.

**Step 3: Re-run test**

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_randomization_config.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/config_values/loco/g1/randomization.py src/holosoma/holosoma/config_values/randomization.py src/holosoma/tests/config_values/test_mjlab_randomization_config.py
git commit -m "feat: add mjlab-safe randomization preset for g1 locomotion"
```

---

## Task 8: Add MJLAB Flat-Terrain Experiment Preset for Phase 1

**Files:**
- Modify: `src/holosoma/holosoma/config_values/loco/g1/experiment.py`
- Modify: `src/holosoma/holosoma/config_values/experiment.py`
- Test: `src/holosoma/tests/config_values/test_mjlab_experiment_config.py`

**Step 1: Write failing experiment config tests**

Add tests for a new experiment preset:
- simulator is MJLAB
- terrain is plane
- randomization uses `g1_29dof_randomization_mjlab`
- action uses MJLAB target-based term

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_experiment_config.py -v`
Expected: FAIL before preset exists.

**Step 2: Implement experiment preset**

Add `g1_29dof_mjlab_flat` experiment and register it in top-level experiment defaults.

**Step 3: Re-run test**

Run: `python -m pytest src/holosoma/tests/config_values/test_mjlab_experiment_config.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/config_values/loco/g1/experiment.py src/holosoma/holosoma/config_values/experiment.py src/holosoma/tests/config_values/test_mjlab_experiment_config.py
git commit -m "feat: add g1 mjlab flat-terrain experiment preset"
```

---

## Task 9: Update Simulator-Type Utility Branches (Including Eval Imports)

**Files:**
- Modify: `src/holosoma/holosoma/utils/draw.py`
- Modify: `src/holosoma/holosoma/utils/sim_utils.py`
- Modify: `src/holosoma/holosoma/utils/eval_utils.py`
- Modify: `src/holosoma/holosoma/simulator/shared/virtual_gantry.py`
- Test: `src/holosoma/tests/simulators/test_mjlab_simulator_type_branches.py`

**Step 1: Write failing utility-branch tests**

Add tests verifying:
- `SimulatorType.MJLAB` does not raise in draw import branch
- simulator import setup handles MJLAB path without Isaac-only side effects
- `eval_utils.init_sim_imports()` remains no-crash for MJLAB
- virtual gantry either supports MJLAB or no-ops with explicit message

Run: `python -m pytest src/holosoma/tests/simulators/test_mjlab_simulator_type_branches.py -v`
Expected: FAIL before utility updates.

**Step 2: Implement utility updates**

Add `MJLAB` handling with MuJoCo-like behavior where appropriate.

**Step 3: Re-run utility tests**

Run: `python -m pytest src/holosoma/tests/simulators/test_mjlab_simulator_type_branches.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/holosoma/holosoma/utils/draw.py src/holosoma/holosoma/utils/sim_utils.py src/holosoma/holosoma/utils/eval_utils.py src/holosoma/holosoma/simulator/shared/virtual_gantry.py src/holosoma/tests/simulators/test_mjlab_simulator_type_branches.py
git commit -m "fix: add mjlab support to simulator-type utility branches"
```

---

## Task 10: Add End-to-End MJLAB Smoke Test and Run Verification

**Files:**
- Create: `src/holosoma/tests/simulators/mjlab/test_mjlab_smoke.py`
- Modify: `src/holosoma/pyproject.toml`

**Step 1: Write failing smoke test**

Add `@pytest.mark.mjlab` integration test that:
- instantiates simulator with G1 MJLAB flat preset
- steps several iterations
- validates no NaNs and expected tensor shapes

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_smoke.py -v -m mjlab`
Expected: FAIL before backend integration is complete.

**Step 2: Add pytest marker**

Register `mjlab` marker under `[tool.pytest.ini_options]`.

**Step 3: Re-run smoke test**

Run: `python -m pytest src/holosoma/tests/simulators/mjlab/test_mjlab_smoke.py -v -m mjlab`
Expected: PASS (in `hsmjlab` environment)

**Step 4: Manual training smoke**

Run:
`python -m holosoma.train_agent exp:g1-29dof-mjlab-flat --training.num-envs 4 --algo.config.num-learning-iterations 100`

Expected:
- startup completes without unsupported randomizer errors
- finite rewards
- stable stepping for at least 100 iterations

**Step 5: Commit**

```bash
git add src/holosoma/tests/simulators/mjlab/test_mjlab_smoke.py src/holosoma/pyproject.toml
git commit -m "test: add mjlab smoke validation and pytest marker"
```

---

## Final Verification Checklist

Activate environment:

```bash
conda activate hsmjlab
```

Run full targeted suite:

```bash
python -m pytest \
  src/holosoma/tests/config_values/test_mjlab_simulator_config.py \
  src/holosoma/tests/config_values/test_mjlab_randomization_config.py \
  src/holosoma/tests/config_values/test_mjlab_experiment_config.py \
  src/holosoma/tests/simulators/mjlab/test_entity_adapter.py \
  src/holosoma/tests/simulators/mjlab/test_state_adapter.py \
  src/holosoma/tests/simulators/mjlab/test_joint_control_mjlab.py \
  src/holosoma/tests/simulators/mjlab/test_mjlab_interface_contract.py \
  src/holosoma/tests/simulators/mjlab/test_mjlab_step_sequence.py \
  src/holosoma/tests/simulators/mjlab/test_mjlab_contact_forces.py \
  src/holosoma/tests/simulators/test_mjlab_simulator_type_branches.py \
  src/holosoma/tests/simulators/mjlab/test_mjlab_smoke.py \
  -v -m "not isaacsim"
```

Expected: all listed tests pass in `hsmjlab` environment.

Manual acceptance:
- `scripts/setup_mjlab.sh` provisions `hsmjlab` with pinned `mjlab==1.1.1`
- `exp:g1-29dof-mjlab-flat` runs with flat terrain and reduced randomization
- bridge path invoking `apply_torques_at_dof()` remains functional
- no regressions in existing non-MJLAB simulator tests
