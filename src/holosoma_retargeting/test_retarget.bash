# python examples/parallel_robot_retarget.py \
# --data-dir demo_data/lafan \
# --task-type robot_only \
# --data_format lafan \
# --save_dir demo_results_parallel/g1/robot_only/lafan \
# --task-config.object-name ground \
# --task-config.ground-range -10 10 \
# --retargeter.foot-sticking-tolerance 0.02 \
# --robot adam_sp \
python examples/robot_retarget.py --data_path demo_data/OMOMO_new_1 \
--task-type robot_only \
--task-name sub3_largebox_003 \
--data_format smplh \
--retargeter.debug \
--retargeter.visualize \
--robot adam_sp \
# --task-config.ground-size 8 \
# --retargeter.n-first-iter 25 \
# --retargeter.n-subsequent-iter 1 \
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

