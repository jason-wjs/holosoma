#!/usr/bin/env python3
"""Filter NPZ files by max body linear speed.

Default behavior:
- Input dir:  src/holosoma_retargeting/holosoma_retargeting/converted_bm/optitrack
- Output dir: src/holosoma_retargeting/holosoma_retargeting/converted_bm/optitrack_filter
- Threshold:  5.0 m/s

Rule:
- If max(||body_lin_vel_w||) > threshold, record the file in report.
- Otherwise copy the file to output dir.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter NPZ files by body_lin_vel_w max speed.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("src/holosoma_retargeting/holosoma_retargeting/converted_bm/optitrack"),
        help="Directory containing input .npz files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for kept files. Defaults to sibling directory named 'optitrack_filter'.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Speed threshold in m/s. Files with max speed above this are recorded as outliers.",
    )
    parser.add_argument(
        "--report-name",
        type=str,
        default="body_lin_vel_over_threshold.txt",
        help="Report filename written under input dir parent.",
    )
    return parser.parse_args()


def max_body_speed(body_lin_vel_w: np.ndarray) -> float:
    """Compute max linear speed from body_lin_vel_w with shape (T, B, 3)."""
    if body_lin_vel_w.ndim != 3 or body_lin_vel_w.shape[-1] != 3:
        raise ValueError(
            f"body_lin_vel_w shape must be (T, B, 3), got {body_lin_vel_w.shape}"
        )
    speed = np.linalg.norm(body_lin_vel_w, axis=-1)  # (T, B)
    return float(np.max(speed))


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if args.output_dir is None:
        output_dir = input_dir.parent / "optitrack_filter"
    else:
        output_dir = args.output_dir.resolve()
    report_path = input_dir.parent / args.report_name

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    npz_files = sorted(input_dir.glob("*.npz"))

    kept = 0
    over_threshold: list[tuple[str, float]] = []
    skipped: list[tuple[str, str]] = []

    for npz_path in npz_files:
        try:
            with np.load(npz_path) as data:
                if "body_lin_vel_w" not in data:
                    skipped.append((npz_path.name, "missing key: body_lin_vel_w"))
                    continue
                max_speed = max_body_speed(data["body_lin_vel_w"])
        except Exception as exc:  # Keep batch processing robust.
            skipped.append((npz_path.name, f"load error: {exc}"))
            continue

        if max_speed > args.threshold:
            over_threshold.append((npz_path.name, max_speed))
        else:
            shutil.copy2(npz_path, output_dir / npz_path.name)
            kept += 1

    over_threshold.sort(key=lambda x: x[1], reverse=True)

    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"input_dir: {input_dir}\n")
        f.write(f"output_dir: {output_dir}\n")
        f.write(f"threshold_mps: {args.threshold}\n")
        f.write(f"total_files: {len(npz_files)}\n")
        f.write(f"kept_files: {kept}\n")
        f.write(f"over_threshold_files: {len(over_threshold)}\n")
        f.write(f"skipped_files: {len(skipped)}\n")
        f.write("\n")
        f.write("[over_threshold]\n")
        for name, max_speed in over_threshold:
            f.write(f"{name}\tmax_speed={max_speed:.6f}\n")
        f.write("\n")
        f.write("[skipped]\n")
        for name, reason in skipped:
            f.write(f"{name}\t{reason}\n")

    print(f"Processed: {len(npz_files)} files")
    print(f"Kept (copied to optitrack_filter): {kept}")
    print(f"Over threshold ({args.threshold} m/s): {len(over_threshold)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
