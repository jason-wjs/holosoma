"""Whole Body Tracking curriculum presets for Adam Pro robot."""

from holosoma.config_types.curriculum import CurriculumManagerCfg, CurriculumTermCfg

adam_pro_29dof_wbt_curriculum = CurriculumManagerCfg(
    params={
        "num_compute_average_epl": 1000,
    },
    setup_terms={
        "average_episode_tracker": CurriculumTermCfg(
            func="holosoma.managers.curriculum.terms.locomotion:AverageEpisodeLengthTracker",
            params={},
        ),
    },
    reset_terms={},
    step_terms={},
)

__all__ = ["adam_pro_29dof_wbt_curriculum"]
