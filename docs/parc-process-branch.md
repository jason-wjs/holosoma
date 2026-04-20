# PARC Process Branch Notes

**Branch:** `parc_process`

## Purpose

This branch adds an offline PARC-to-G1 bootstrap pipeline inside the `holosoma` fork.

The branch goal is narrow and explicit:

- read PARC `initial_aug` humanoid terrain-motion pairs
- reconstruct source humanoid joint trajectories from `motion_data`
- export PARC terrain into MuJoCo assets that `holosoma_retargeting` can consume
- retarget the source motion to Unitree G1
- write paired G1 dataset artifacts for downstream `parc_g1` consumption

This branch is not intended to train or evaluate PARC inside `holosoma`. It is the upstream data-compilation step that produces bootstrap data for the downstream `parc_g1` project.

## Why It Lives In `holosoma`

The conversion path depends on the existing `holosoma_retargeting` solver, robot models, and scene handling. Keeping the PARC-source parsing and workspace assembly here gives a clean repository boundary:

- `holosoma/parc_process`
  - consumes PARC source assets
  - performs source FK and terrain export
  - runs the G1 retargeter
  - writes paired G1 outputs
- `parc_g1`
  - consumes the compiled paired dataset
  - focuses on tracker, training, evaluation, and iteration

This keeps `parc_g1` free of PARC-specific source parsing and retargeting assembly logic.

## Implemented Pieces

The branch currently adds the following PARC-specific path inside `holosoma_retargeting`:

- `parc_process/source_io.py`
  - loads PARC `initial_aug` `.pkl` samples into normalized source objects
- `parc_process/source_fk.py`
  - reconstructs source humanoid world-space joints from `motion_data` and `humanoid.xml`
- `parc_process/terrain_scene.py`
  - exports `terrain_data.hf` into static `.obj`, MuJoCo XML assets, and a visualization URDF
- `parc_process/workspace.py`
  - assembles per-sample retargeting workspaces
- `parc_process/output_writer.py`
  - writes final paired G1 `.pkl` files and a `motions.yaml` manifest
- `examples/parc_process.py`
  - provides the CLI entrypoint for running the compilation flow

The branch also extends the retargeting configuration with a `parc_humanoid` source format and a PARC-humanoid to G1 joint mapping.

## Current Output Contract

There are two kinds of outputs in this branch:

1. Intermediate retarget outputs
   - `retargeted/*.npz`
   - these are solver outputs used for inspection and visualization
   - these are not the final artifacts that `parc_g1` should consume directly

2. Final paired outputs
   - one `*_g1.pkl` file per converted sample
   - one `motions.yaml` manifest
   - these are the artifacts intended for downstream consumption

The paired output keeps the original PARC `terrain_data` and writes G1-side motion data plus provenance metadata needed for later debugging.

## Current Constraint Setting

The branch is currently validated with a relaxed retargeting setup:

- joint limits enabled
- default retargeting optimizer enabled
- `foot_sticking` enabled
- object or terrain non-penetration disabled by default in the PARC path
- foot lock disabled
- self collision disabled

This is an intentional bootstrap setting. It prioritizes stable conversion over strict contact enforcement.

In practice, the relaxed setting is enough to preserve the source motion semantics on the tested samples, but occasional visible foot penetration can still remain in visualization.

## Validated Samples

The branch has been exercised on real PARC `initial_aug` samples, including:

- `platform/platform_001.pkl`
- `mid_climbing/mid_blocks_004_dm.pkl`
- `platform/beyond_platform_002.pkl`
- `platform/beyond_platform_004.pkl`

These were converted successfully through the full path:

- source `.pkl`
- terrain export and workspace assembly
- G1 retargeting
- intermediate `.npz`
- final paired `*_g1.pkl`
- `motions.yaml`

## Known Limitation

The main current limitation is contact strictness.

Turning on terrain or object non-penetration for the tested samples can make the solve fail early, while the relaxed setting completes successfully. That means this branch currently solves the bootstrap problem, but it does not yet guarantee strict terrain-consistent foot contact for every frame.

This is acceptable for the current project stage because the immediate objective is to establish a working G1 simulation bootstrap pipeline in `mjlab`, not to solve final contact refinement inside the retargeter.

## Running The Pipeline

The branch is meant to run inside the existing `hsretargeting` environment.

Example:

```bash
cd /home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/holosoma
source scripts/source_retargeting_setup.sh

python src/holosoma_retargeting/holosoma_retargeting/examples/parc_process.py \
  --sample /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl \
  --source-xml /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml \
  --output-root /tmp/parc_process_bootstrap \
  --retarget-save-dir /tmp/parc_process_workspace
```

Expected outputs:

- `/tmp/parc_process_workspace/workspace/<task>/...`
- `/tmp/parc_process_workspace/retargeted/<task>_original.npz`
- `/tmp/parc_process_bootstrap/<task>_g1.pkl`
- `/tmp/parc_process_bootstrap/motions.yaml`

## Visual Inspection

The intermediate `.npz` files can be inspected with `viser_player.py`.

Important note: the PARC retargeted `.npz` files produced by this branch do not append an object pose tail, so visualization should use:

```bash
--assume-object-in-qpos False
```

Without that flag, the viewer can misread the final robot dimensions as object state.

## Test Coverage

The branch includes focused tests for the new PARC path, including:

- CLI behavior
- source-pose initialization
- solver-side non-penetration gating
- terrain scene export

These tests are intended to guard the bootstrap flow without trying to fully regression-test all of `holosoma_retargeting`.

## Relationship To `parc_g1`

This branch should be treated as an upstream compiler for `parc_g1`.

The intended handoff is:

1. Convert PARC `initial_aug` source samples into paired G1 outputs here.
2. Point `parc_g1` dataset configuration at the generated `motions.yaml`.
3. Continue tracker-side terrain-aware work in `mjlab` on top of the converted G1 paired dataset.

That separation is deliberate. The retargeting and source-data adaptation problem is handled here once, while `parc_g1` stays focused on the actual simulation and learning stack.
