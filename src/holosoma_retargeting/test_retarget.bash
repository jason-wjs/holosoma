python examples/robot_retarget.py --data_path demo_data/OMOMO_new_1 \
--task-type robot_only \
--task-name sub3_largebox_003 \
--data_format smplh \
--retargeter.debug \
--retargeter.visualize \
--task-config.ground-size 8 \
--retargeter.n-first-iter 50 \
--retargeter.n-subsequent-iter 10 \
--retargeter.step-size 0.2 \
--robot adam_sp
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

