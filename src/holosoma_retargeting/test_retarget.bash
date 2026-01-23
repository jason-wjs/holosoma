conda activate hsretargeting
## for adam_sp lafan default urdf path is models/adam_sp/adam_sp_29dof.urdf
# python examples/parallel_robot_retarget.py \
# --data-dir demo_data/lafan \
# --task-type robot_only \
# --data_format lafan \
# --save_dir demo_results_parallel/adam_sp/robot_only/lafan \
# --task-config.object-name ground \
# --task-config.ground-range -10 10 \
# --retargeter.foot-sticking-tolerance 0.02 \
# --robot adam_sp \
## for adam_sp bvh default urdf path is models/adam_sp/adam_sp_29dof.urdf
python examples/robot_retarget.py \
--data_path demo_data/converted_bvh \
--task-type robot_only \
--task-name "CYCLE3_Skeleton_z_up_x_forward_gym" \
--data_format bvh \
--robot adam_sp \
--save_dir demo_results/adam_sp/robot_only/converted_bvh \
--retargeter.n-first-iter 50 \
--retargeter.n-subsequent-iter 5 \
--retargeter.smooth-weight 0.2 \
--retargeter.debug \
--retargeter.visualize \
--retargeter.step-size 0.2 \
# --retargeter.no-activate-foot-sticking
# --retargeter.no-activate-obj-non-penetration \ # deactivate obj non penetration
# --retargeter.no-activate-foot-sticking \ # deactivate foot sticking
# --retargeter.no-activate-joint-limits \ # deactivate joint limits

## for g1 default urdf path is models/g1/g1_29dof.urdf
# python examples/robot_retarget.py \
# --data_path demo_data/converted_bvh \
# --task-type robot_only \
# --task-name "gym_022" \
# --data_format bvh \
# --robot adam_sp \
# --save_dir demo_results/g1/robot_only/converted_bvh \
# --retargeter.n-first-iter 25 \
# --retargeter.n-subsequent-iter 1 \
# --retargeter.smooth-weight 2.0 \
# --retargeter.debug \
# --retargeter.visualize \
# --retargeter.step-size 0.1 \


# --retargeter.no-activate-obj-non-penetration \
# --retargeter.visualize \
# --retargeter.no-debug \
# --retargeter.no-activate-joint-limits \
# python examples/robot_retarget.py \
# --data_path demo_data/lafan \
# --task-type robot_only \
# --task-name dance1_subject1 \
# --data_format lafan \
# --save_dir demo_results_parallel/g1/robot_only/lafan \
# --task-config.object-name ground \
# --task-config.ground-range -10 10 \
# --retargeter.foot-sticking-tolerance 0.02 \
# --robot adam_sp \
# --retargeter.debug \
# --retargeter.visualize \
# python examples/robot_retarget.py --data_path demo_data/OMOMO_new \
# --task-type robot_only \
# --task-name sub3_largebox_003 \
# --data_format smplh \
# --retargeter.debug \
# --retargeter.visualize \
# --retargeter.foot-sticking-tolerance 5e-3 \
# --robot adam_sp \
# --task-config.ground-size 5 \
# python examples/robot_retarget.py \
# --data_path demo_data/climb \
# --task-type climbing \
# --task-name mocap_climb_seq_0 \
# --data_format mocap --robot adam_sp \
# --robot-config.robot-urdf-file models/adam_sp/adam_sp_29dof_spherehand.urdf \
# --retargeter.debug \
# --retargeter.visualize \
# --retargeter.foot-sticking-tolerance 1e-3 \
# --save-dir demo_results/adam_sp/climbing/mocap_climb_new
# --retargeter.n-first-iter 25 \
# --retargeter.n-subsequent-iter 5 \
# --retargeter.step-size 0.2 \
# --retargeter.smooth-weight 0.5 \
# python examples/parallel_robot_retarget.py \
# --data-dir demo_data/OMOMO_new \
# --task-type robot_only \
# --data_format smplh \
# --save_dir demo_results_parallel/g1/robot_only/omomo \
# --task-config.object-name ground \
# --max-workers 10 \
# --retargeter.n-first-iter 25 \
# --retargeter.n-subsequent-iter 1 \
# - -retargeter.step-size 0.4
# --retargeter.no-activate-foot-sticking \
# --retargeter.no-activate-obj-non-penetration \
# --retargeter.no-activate-joint-limits \
# --retargeter.no-activate-obj-non-penetration \
# --retargeter.max-penetration-constraints 10 \

