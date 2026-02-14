"""Whole Body Tracking curriculum presets for Adam Pro robot."""

from holosoma.config_types.curriculum import CurriculumManagerCfg, TermCfg

adam_pro_29dof_wbt_curriculum = CurriculumManagerCfg(
    terms={
        "adaptive_sampling": TermCfg(
            func="holosoma.managers.curriculum.terms.wbt:adaptive_timestep_sampling",
            params={
                "num_bins": 30,  # 1-second bins for 50fps motion (30 bins * 50fps = 1500 frames ≈ 30s)
                "kernel_std": 2.0,  # Smoothing for adaptive sampling distribution
            },
        ),
    },
)

__all__ = ["adam_pro_29dof_wbt_curriculum"]