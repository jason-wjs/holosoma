# Holosoma Motion Retargeting

This repository provides tools for retargeting human motion data to humanoid robots. It supports multiple data formats (smplh, mocap, lafan) and task types including robot-only motion, object interaction, and climbing.

**Data Requirements**: The retargeting pipeline requires motion data in world joint positions. For custom data, you need to prepare world joint positions in shape `(T, J, 3)` where T is the number of frames and J is the number of joints, and modify `demo_joints` and `joints_mapping` defined in `config_types/data_type.py`.
## conda environment
```bash
conda activate  hsretargeting
```
## key file
```bash
/home/humanoid/yzh/holosoma/src/holosoma_retargeting/config_types/data_type.py # data_type config of retargeting
```
JOINTS_MAPPINGS
```python
    ("bvh", "adam_sp"): {
        "Hips": "pelvis",
        "LeftUpLeg": "thighLeft",
        "RightUpLeg": "thighRight",
        "LeftLeg": "shinLeft",
        "RightLeg": "shinRight",
        "LeftArm": "shoulderPitchLeft",
        "RightArm": "shoulderPitchRight",
        "LeftForeArm": "elbowLeft",
        "RightForeArm": "elbowRight",
        "LeftFoot": "toeLeft",
        "RightFoot": "toeRight",
        "LeftToeBase": "toeTipLeft",
        "RightToeBase": "toeTipRight",
        "LeftHand": "wristRollLeft",
        "RightHand": "wristRollRight",
    },
``` 
/home/humanoid/yzh/holosoma/src/holosoma_retargeting/examples/robot_retarget.py API of retargeting


/home/humanoid/yzh/holosoma/src/holosoma_retargeting/src/interaction_mesh_retargeter.py optimization main file

/home/humanoid/yzh/holosoma/src/holosoma_retargeting/config_types/robot.py manual paramters of cost lower bound and upper bound
```python
    def _manual_cost(self) -> dict[str, float]:
        """Get manual cost weights."""
        if self.manual_cost is not None:
            return self.manual_cost

        if self.robot_type == "g1":
            return {"19": 0.2, "20": 0.2}  # waist roll , waist pitch
        if self.robot_type == "adam_sp":
            ## add manual cost for foot and toe
            return {
                # "8": 0.1,  # hipRoll_Left
                # "9": 0.1,  # hipYaw_Left
                # "11": 0.5, # ankle pitch left
                # "12": 0.5, # ankle roll left
                # "17": 0.5, # ankle pitch right
                # "18": 0.5, # ankle roll right
                # "14": 0.1,  # hipRoll_Right
                # "15": 0.1,  # hipYaw_Right
                "19": 0.2,  # waistRoll
                "20": 0.2,  # waistPitch
                "21": 0.2,  # waistYaw
            }
        return {}
``` 
## Single Sequence Motion Retargeting
```bash
# Robot-only (OMOMO) on ADAM-SP
python examples/robot_retarget.py --data_path demo_data/OMOMO_new --task-type robot_only --task-name sub3_largebox_003 --data_format smplh --retargeter.debug --retargeter.visualize --robot adam_sp

# Object interaction (OMOMO) on ADAM-SP
python examples/robot_retarget.py --data_path demo_data/OMOMO_new --task-type object_interaction --task-name sub3_largebox_003 --data_format smplh --robot adam_sp --retargeter.debug --retargeter.visualize

# Climbing on ADAM-SP
python examples/robot_retarget.py --data_path demo_data/climb --task-type climbing --task-name mocap_climb_seq_0 --data_format mocap --robot adam_sp --robot-config.robot-urdf-file models/adam_sp/adam_sp_29dof_spherehand.urdf --retargeter.debug --retargeter.visualize
```

**Note**: Add `--augmentation` to run sequences with augmentation. You must first run the original sequence before adding augmentation.

## Batch Processing for Motion Retargeting

```bash
# Robot-only (OMOMO) on ADAM-SP
python examples/parallel_robot_retarget.py --data-dir demo_data/OMOMO_new --task-type robot_only --data_format smplh --save_dir demo_results_parallel/g1/robot_only/omomo --task-config.object-name ground --robot adam_sp

# Object interaction (OMOMO) on ADAM-SP
python examples/parallel_robot_retarget.py --data-dir demo_data/OMOMO_new --task-type object_interaction --data_format smplh --save_dir demo_results_parallel/adam_sp/object_interaction/omomo --task-config.object-name largebox --robot adam_sp

# Climbing on ADAM-SP
python examples/parallel_robot_retarget.py --data-dir demo_data/climb --task-type climbing --data_format mocap --task-config.object-name multi_boxes --save_dir demo_results_parallel/adam_sp/climbing/mocap_climb --robot adam_sp --robot-config.robot-urdf-file models/adam_sp/adam_sp_29dof_spherehand.urdf
```

**Note**: Add `--augmentation` to run original sequences and sequences with augmentation (for object interaction and climbing tasks).

## Data Preparation

We provide `demo_data/` for fast testing. To test on more motion sequences, please follow the instructions below to download and prepare the data.

### OMOMO

Our pipeline uses the processed dataset by InterMimic. The data format differs from the original OMOMO dataset.

1. Download the processed OMOMO data from [this link](https://drive.google.com/file/d/141YoPOd2DlJ4jhU2cpZO5VU5GzV_lm5j/view)
2. Extract the downloaded folder to `demo_data/OMOMO_new`

The data should contain `.pt` files.

### LAFAN

#### Download the Original LAFAN Data

1. Download [lafan1.zip](https://github.com/ubisoft/ubisoft-laforge-animation-dataset/blob/master/lafan1/lafan1.zip) by clicking "View Raw"
2. Put `lafan1.zip` in your designated data folder and uncompress it to `DATA_FOLDER_PATH/lafan`
3. The file structure should be `demo_data/lafan/*.bvh`

#### Convert the Original LAFAN Data Format for Motion Retargeting

We need some data processing files from the [LAFAN GitHub repo](https://github.com/ubisoft/ubisoft-laforge-animation-dataset).

```bash
cd holosoma_retargeting/data_utils/
git clone https://github.com/ubisoft/ubisoft-laforge-animation-dataset.git
mv ubisoft-laforge-animation-dataset/lafan1 .
python extract_global_positions.py --input_dir DATA_FOLDER_PATH/lafan --output_dir ../demo_data/lafan
```

This will convert the BVH files to `.npy` format with global joint positions.

**Note**: For LAFAN data, you need to relax the foot sticking constraint by setting `--retargeter.foot-sticking-tolerance` (default is stricter). You can adjust this tolerance number based on your data quality and retargeting results.

#### Single Sequence Retargeting on LAFAN

```bash
python examples/robot_retarget.py --data_path demo_data/lafan --task-type robot_only --task-name dance2_subject1 --data_format lafan --task-config.ground-range -10 10 --save_dir demo_results/g1/robot_only/lafan --retargeter.debug --retargeter.visualize --retargeter.foot-sticking-tolerance 0.02
```

#### Batch Processing for Motion Retargeting on LAFAN

```bash
python examples/parallel_robot_retarget.py --data-dir demo_data/lafan --task-type robot_only --data_format lafan --save_dir demo_results_parallel/g1/robot_only/lafan --task-config.object-name ground --task-config.ground-range -10 10 --retargeter.foot-sticking-tolerance 0.02
```

## Check Visualizations of Saved Retargeting Results

```bash
# Visualize object-interaction results
python viser_player.py --robot_urdf models/g1/g1_29dof.urdf \
    --object_urdf models/largebox/largebox.urdf \
    --qpos_npz demo_results_parallel/g1/object_interaction/omomo/sub3_largebox_003_original.npz

# Visualize climbing results
python viser_player.py --robot_urdf models/g1/g1_29dof_spherehand.urdf \
    --object_urdf demo_data/climb/mocap_climb_seq_0/multi_boxes.urdf \
    --qpos_npz demo_results_parallel/g1/climbing/mocap_climb/mocap_climb_seq_0_original.npz

python viser_player.py --robot_urdf models/g1/g1_29dof_spherehand.urdf \
    --object_urdf demo_data/climb/mocap_climb_seq_0/multi_boxes_scaled_0.74_0.74_0.89.urdf \
    --qpos_npz demo_results_parallel/g1/climbing/mocap_climb/mocap_climb_seq_0_z_scale_1.2.npz

# Visualize robot only results
python viser_player.py --robot_urdf models/g1/g1_29dof.urdf \
    --qpos_npz demo_results_parallel/g1/robot_only/omomo/sub3_largebox_003_original.npz

# Visualize LAFAN robot only results
python viser_player.py --robot_urdf models/g1/g1_29dof.urdf \
    --qpos_npz demo_results/g1/robot_only/lafan/dance2_subject1.npz
```

## Quantitative Evaluation

```bash
# Evaluate robot-object interaction
python evaluation/eval_retargeting.py --res_dir demo_results_parallel/g1/object_interaction/omomo --data_dir demo_data/OMOMO_new --data_type "robot_object"

# Evaluate climbing sequence
python evaluation/eval_retargeting.py --res_dir demo_results_parallel/g1/climbing/mocap_climb --data_dir demo_data/climb --data_type "robot_terrain" --robot-config.robot-urdf-file models/g1/g1_29dof_spherehand.urdf

# Evaluate robot only (OMOMO)
python evaluation/eval_retargeting.py --res_dir demo_results_parallel/g1/robot_only/omomo --data_dir demo_data/OMOMO_new --data_type "robot_only"
```

## Prepare Data for Training RL Whole-Body Tracking Policy

To prepare data for training RL whole-body tracking policies, you need to follow a two-step process:

1. **First, run retargeting** to obtain `.npz` files containing the retargeted robot motion. Use the retargeting commands shown in the sections above (Single Sequence Motion Retargeting or Batch Processing for Motion Retargeting).

2. **Then, run the data conversion code** below to convert the retargeted `.npz` files into the format required for RL training. The conversion script takes the retargeted `.npz` files as input and outputs converted files with the specified frame rate and format.

**Note**: If you run this code on Mac, please use `mjpython` instead of `python`.

### Mac (using mjpython)

```bash
mjpython data_conversion/convert_data_format_mj.py --input_file ./demo_results/g1/robot_only/omomo/sub3_largebox_003.npz --output_fps 50 --output_name converted_res/robot_only/sub3_largebox_003_mj_fps50.npz --data_format smplh --object_name "ground" --once

mjpython data_conversion/convert_data_format_mj.py --input_file ./demo_results/g1/object_interaction/omomo/sub3_largebox_003_original.npz --output_fps 50 --output_name converted_res/object_interaction/sub3_largebox_003_mj_w_obj.npz --data_format smplh --object_name "largebox" --has_dynamic_object --once
```
我需要另外一个 test 文件，去检测 adam 两个手腕的末端位置 和 bvh中 body 的末端位置之间的偏差，你最好能帮我把BVH original human body 也可视化在viser 中，请你帮我写一个可视化脚本 对比一下。
### Robot-Only Setting
```bash
python data_conversion/convert_data_format_mj.py --input_file demo_results/adam_sp/robot_only/bvh_0110/balance_001_Skeleton_006_z_up_x_forward_gym.npz --output_fps 50 --output_name converted_res/robot_only/adam_sp --data_format bvh  --robot adam_sp --object_name "ground" --once
```bash
python data_conversion/convert_data_format_mj.py --input_file ./demo_results/g1/robot_only/omomo/sub3_largebox_003.npz --output_fps 50 --output_name converted_res/robot_only/sub3_largebox_003_mj_fps50.npz --data_format smplh --object_name "ground" --once

python data_conversion/convert_data_format_mj.py --input_file ./demo_results/g1/robot_only/lafan/dance2_subject1.npz --output_fps 50 --output_name converted_res/robot_only/dance2_subject1_mj_fps50.npz --data_format lafan --object_name "ground" --once
```

### Robot-Object Setting

```bash
python data_conversion/convert_data_format_mj.py --input_file ./demo_results/g1/object_interaction/omomo/sub3_largebox_003_original.npz --output_fps 50 --output_name converted_res/object_interaction/sub3_largebox_003_mj_w_obj.npz --data_format smplh --object_name "largebox" --has_dynamic_object --once
```

### OmniRetarget Data

For OmniRetarget data downloaded from HuggingFace, please add `--use_omniretarget_data` for data conversion.

```bash
python data_conversion/convert_data_format_mj.py --input_file OmniRetarget/robot-object/sub3_largebox_003_original.npz --output_fps 50 --output_name converted_res/object_interaction/sub3_largebox_003_mj_w_obj_omnirt.npz --data_format smplh --object_name "largebox" --has_dynamic_object --use_omniretarget_data --once
```
