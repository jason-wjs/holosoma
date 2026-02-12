# Adam Pro Retargeting (Robot-Only) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `adam_pro` as a first-class retargeting robot for `robot_only + ground`, using a **retargeting model** under `models/adam_pro/` derived from `adam_pro/adam_pro_29dof.xml` with minimal, controlled edits.

**Architecture:** Use `adam_pro/adam_pro_29dof.xml` as a seed and perform a constrained refinement: remove only `sensor` and `actuator` sections, keep kinematic chain/body names/joint limits/collision structure unchanged, and leave structure ready for marker additions later. Pair it with a matching `adam_pro_29dof.urdf`, register robot defaults, add motion mappings, and validate with tests plus one CLI smoke run.

**Tech Stack:** Python 3.10+, MuJoCo, Tyro config dataclasses, PyTest, XML/URDF parsing via stdlib (`xml.etree.ElementTree`).

### Task 1: Define Model Refinement Contract (Test First)

**Files:**
- Create: `src/holosoma_retargeting/tests/test_adam_pro_model_refinement_contract.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
import xml.etree.ElementTree as ET

MODEL_XML = Path("holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml")

EXPECTED_29 = [
    "hipPitch_Left", "hipRoll_Left", "hipYaw_Left", "kneePitch_Left", "anklePitch_Left", "ankleRoll_Left",
    "hipPitch_Right", "hipRoll_Right", "hipYaw_Right", "kneePitch_Right", "anklePitch_Right", "ankleRoll_Right",
    "waistRoll", "waistPitch", "waistYaw",
    "shoulderPitch_Left", "shoulderRoll_Left", "shoulderYaw_Left", "elbow_Left", "wristYaw_Left", "wristPitch_Left", "wristRoll_Left",
    "shoulderPitch_Right", "shoulderRoll_Right", "shoulderYaw_Right", "elbow_Right", "wristYaw_Right", "wristPitch_Right", "wristRoll_Right",
]


def test_refined_xml_exists():
    assert MODEL_XML.is_file()


def test_refined_xml_has_expected_joint_set_and_order():
    root = ET.parse(MODEL_XML).getroot()
    names = [j.attrib["name"] for j in root.findall(".//joint") if "name" in j.attrib and j.attrib["name"] != "floating_base"]
    assert names == EXPECTED_29


def test_refined_xml_drops_retargeting_irrelevant_sections():
    root = ET.parse(MODEL_XML).getroot()
    assert root.find("actuator") is None
    assert root.find("sensor") is None
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_model_refinement_contract.py -q
```

Expected: FAIL (refined model missing).

**Step 3: Commit test scaffold (optional if policy is strict TDD commits)**

```bash
git add src/holosoma_retargeting/tests/test_adam_pro_model_refinement_contract.py
git commit -m "test(retargeting): define adam_pro refined model contract"
```

### Task 2: Create Refined Retargeting XML From Seed

**Files:**
- Create/Modify: `src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml`
- Create/Copy: `src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/meshes/*`

**Step 1: Seed and refine XML**

- Seed from: `adam_pro/adam_pro_29dof.xml`.
- Place working copy at: `models/adam_pro/adam_pro_29dof.xml`.
- Refine with constrained scope:
  - Keep exactly as-is: body tree, inertials, 29 joints, joint ranges, free base, body names, contact/collision, defaults, camera/light, and any existing supporting structure.
  - Remove only: `actuator`, `sensor`.
  - Do not remove/reshape other sections in this phase.
  - Preserve mesh references with `meshdir="meshes"` and copy required mesh files.

**Step 2: Run contract test**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_model_refinement_contract.py -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/models/adam_pro src/holosoma_retargeting/tests/test_adam_pro_model_refinement_contract.py
git commit -m "feat(retargeting): add refined adam_pro 29dof xml model"
```

### Task 3: Add Matching 29-DoF URDF (Aligned With Refined XML)

**Files:**
- Create: `src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/adam_pro_29dof.urdf`
- Create: `src/holosoma_retargeting/tests/test_adam_pro_xml_urdf_consistency.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
import xml.etree.ElementTree as ET

XML = Path("holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml")
URDF = Path("holosoma_retargeting/models/adam_pro/adam_pro_29dof.urdf")


def _xml_joint_names():
    root = ET.parse(XML).getroot()
    return [j.attrib["name"] for j in root.findall(".//joint") if j.attrib.get("name") != "floating_base"]


def _urdf_revolute_joint_names():
    root = ET.parse(URDF).getroot()
    return [j.attrib["name"] for j in root.findall("joint") if j.attrib.get("type") == "revolute"]


def test_urdf_exists():
    assert URDF.is_file()


def test_xml_urdf_joint_order_match_exactly():
    assert _urdf_revolute_joint_names() == _xml_joint_names()
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_xml_urdf_consistency.py -q
```

Expected: FAIL (URDF missing or mismatch).

**Step 3: Implement matching URDF**

- Create `adam_pro_29dof.urdf` with exactly the same 29 articulated joints and ordering as refined XML.
- Keep neck/fingers non-articulated.
- Ensure all mapped body/link names exist for retargeting and visualization.

**Step 4: Run test to verify it passes**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_xml_urdf_consistency.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/adam_pro_29dof.urdf src/holosoma_retargeting/tests/test_adam_pro_xml_urdf_consistency.py
git commit -m "feat(retargeting): add adam_pro 29dof urdf aligned with refined xml"
```

### Task 4: Register Adam Pro Robot Defaults

**Files:**
- Modify: `src/holosoma_retargeting/holosoma_retargeting/config_types/robot.py`
- Create: `src/holosoma_retargeting/tests/test_adam_pro_robot_config.py`

**Step 1: Write the failing test**

```python
from holosoma_retargeting.config_types.robot import RobotConfig


def test_adam_pro_defaults_registered():
    cfg = RobotConfig(robot_type="adam_pro")
    assert cfg.ROBOT_DOF == 29
    assert cfg.ROBOT_NAME == "adam_pro_29dof"
    assert cfg.ROBOT_URDF_FILE == "models/adam_pro/adam_pro_29dof.urdf"


def test_adam_pro_has_foot_links_for_sticking():
    cfg = RobotConfig(robot_type="adam_pro")
    assert len(cfg.FOOT_STICKING_LINKS) >= 2
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_robot_config.py -q
```

Expected: FAIL with invalid robot type.

**Step 3: Implement defaults**

- Add `adam_pro` to `_ROBOT_DEFAULTS` with `robot_dof=29`, `object_name="ground"`.
- Add `_foot_sticking_links()` branch using existing reliable links (initially `toeLeft`, `toeRight`; tune later).

**Step 4: Run test to verify it passes**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_robot_config.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/config_types/robot.py src/holosoma_retargeting/tests/test_adam_pro_robot_config.py
git commit -m "feat(retargeting): register adam_pro robot defaults"
```

### Task 5: Add Adam Pro Motion Mappings

**Files:**
- Modify: `src/holosoma_retargeting/holosoma_retargeting/config_types/data_type.py`
- Create: `src/holosoma_retargeting/tests/test_adam_pro_motion_mappings.py`

**Step 1: Write the failing test**

```python
from holosoma_retargeting.config_types.data_type import MotionDataConfig


def test_adam_pro_mapping_exists_for_smplh_smplx_lafan():
    for fmt in ("smplh", "smplx", "lafan"):
        cfg = MotionDataConfig(data_format=fmt, robot_type="adam_pro")
        assert len(cfg.resolved_joints_mapping) > 0
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_motion_mappings.py -q
```

Expected: FAIL with missing mapping.

**Step 3: Implement mappings**

- Add `("smplh", "adam_pro")`, `("smplx", "adam_pro")`, `("lafan", "adam_pro")` in `JOINTS_MAPPINGS`.
- Use body names that exist in refined XML (pelvis/hip/knee/toe/shoulder/elbow/wrist bodies).

**Step 4: Run test to verify it passes**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_motion_mappings.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/config_types/data_type.py src/holosoma_retargeting/tests/test_adam_pro_motion_mappings.py
git commit -m "feat(retargeting): add adam_pro motion mappings"
```

### Task 6: Add Canonical Adam Pro Joint Order For Data Conversion

**Files:**
- Modify: `src/holosoma_retargeting/holosoma_retargeting/config_types/data_conversion.py`
- Create: `src/holosoma_retargeting/tests/test_adam_pro_data_conversion.py`

**Step 1: Write the failing test**

```python
from holosoma_retargeting.config_types.data_conversion import DataConversionConfig


def test_adam_pro_joint_order_available_and_29dof():
    cfg = DataConversionConfig(input_file="dummy.npz", robot="adam_pro")
    names = cfg.JOINT_NAMES
    assert len(names) == 29
    assert len(set(names)) == 29
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_data_conversion.py -q
```

Expected: FAIL with missing robot joint names.

**Step 3: Implement**

- Add `"adam_pro"` to `_ROBOT_JOINT_NAMES_DEFAULT` with exact order from refined XML.

**Step 4: Run test to verify it passes**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_data_conversion.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/config_types/data_conversion.py src/holosoma_retargeting/tests/test_adam_pro_data_conversion.py
git commit -m "feat(retargeting): add adam_pro conversion joint order"
```

### Task 7: Robot-Only CLI Smoke Validation

**Files:**
- Create: `src/holosoma_retargeting/tests/test_adam_pro_cli_smoke.py`

**Step 1: Write failing smoke test**

```python
from pathlib import Path
import numpy as np


def test_robot_only_smoke_output_exists_and_shape_matches():
    out = Path("/tmp/adam_pro_rt_smoke/sub3_largebox_003.npz")
    assert out.is_file()
    qpos = np.load(out)["qpos"]
    assert qpos.shape[1] == 36  # 7 + 29
```

**Step 2: Verify failing**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_cli_smoke.py -q
```

Expected: FAIL (no output file yet).

**Step 3: Run smoke retargeting**

Run:
```bash
cd src/holosoma_retargeting/holosoma_retargeting
python examples/robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-name sub3_largebox_003 \
  --data_path demo_data/OMOMO_new \
  --data_format smplh \
  --save_dir /tmp/adam_pro_rt_smoke
```

Expected: output file at `/tmp/adam_pro_rt_smoke/sub3_largebox_003.npz`.

**Step 4: Verify passing**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_cli_smoke.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/tests/test_adam_pro_cli_smoke.py
git commit -m "test(retargeting): add adam_pro robot-only smoke validation"
```

### Task 8: Final Verification Gate

**Files:**
- Verify only

**Step 1: Run targeted test bundle**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest \
  tests/test_adam_pro_model_refinement_contract.py \
  tests/test_adam_pro_xml_urdf_consistency.py \
  tests/test_adam_pro_robot_config.py \
  tests/test_adam_pro_motion_mappings.py \
  tests/test_adam_pro_data_conversion.py \
  tests/test_adam_pro_cli_smoke.py -q
```

Expected: PASS.

**Step 2: Optional conversion smoke**

Run:
```bash
cd src/holosoma_retargeting/holosoma_retargeting
python data_conversion/convert_data_format_mj.py \
  --input_file /tmp/adam_pro_rt_smoke/sub3_largebox_003.npz \
  --output_fps 50 \
  --output_name /tmp/adam_pro_rt_smoke/sub3_largebox_003_mj_fps50.npz \
  --data_format smplh \
  --robot adam_pro \
  --object_name ground \
  --once
```

Expected: converted output generated without robot/mapping errors.

### Task 9: Marker-Ready Preparation (No Marker Implementation)

**Files:**
- Modify: `src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml` (comments only)
- Create: `src/holosoma_retargeting/tests/test_adam_pro_marker_readiness.py`

**Step 1: Write failing test for marker-readiness metadata**

```python
from pathlib import Path


def test_marker_ready_todo_present_in_model_header():
    text = Path("holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml").read_text()
    assert "MARKER_READY_TODO" in text
```

**Step 2: Verify failing**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_marker_readiness.py -q
```

Expected: FAIL (placeholder not present yet).

**Step 3: Add explicit marker-ready TODO block**

- Add a short XML comment near file header, documenting:
  - intended future marker entry points for feet/hands
  - requirement to keep current body names stable for backward compatibility
  - note that no markers are added in this phase

**Step 4: Verify passing**

Run:
```bash
cd src/holosoma_retargeting
python -m pytest tests/test_adam_pro_marker_readiness.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml src/holosoma_retargeting/tests/test_adam_pro_marker_readiness.py
git commit -m "chore(retargeting): annotate adam_pro model for future marker extension"
```

## Non-Goals (This Plan)

- No object interaction / climbing.
- No marker/spherehand/largebox variants yet.
- No training stack edits.

## Follow-Up Phase

1. Add marker-enhanced Adam Pro retargeting variants.
2. Tune foot-sticking links beyond `toeLeft/toeRight`.
3. Add Adam Pro scene variants for object/climbing tasks.
