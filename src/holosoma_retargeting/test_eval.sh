# python evaluation/eval_retargeting.py \
# --res_dir demo_results_parallel/g1/robot_only/omomo \
# --data_dir demo_data/OMOMO_new/ \
# --data_type "robot_only"
python evaluation/eval_retargeting.py \
--res_dir demo_results/adam_sp/robot_only/omomo \
--data_dir demo_data/OMOMO_new \
--data_type "robot_only" \
--robot adam_sp \
--robot-config.robot-urdf-file models/adam_sp/adam_sp_29dof.urdf 