#!/usr/bin/env python3
"""批量可视化一个文件夹中的所有 npz 文件"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


def find_npz_files(directory: str) -> list[Path]:
    """在目录中查找所有 npz 文件"""
    npz_dir = Path(directory)
    if not npz_dir.exists():
        print(f"错误: 目录不存在: {directory}")
        return []
    
    npz_files = sorted(npz_dir.glob("*.npz"))
    return npz_files


def visualize_npz(npz_path: Path, robot_type: str, robot_urdf: str, vel_scale: float = 0.1):
    """可视化单个 npz 文件"""
    script_dir = Path(__file__).parent
    player_script = script_dir / "viser_body_vel_player.py"
    
    if not player_script.exists():
        print(f"错误: 找不到播放器脚本: {player_script}")
        return False
    
    print(f"\n{'='*60}")
    print(f"正在可视化: {npz_path.name}")
    print(f"{'='*60}")
    
    cmd = [
        "python",
        str(player_script),
        "--npz_path", str(npz_path),
        "--robot_urdf", robot_urdf,
        "--robot_type", robot_type,
        "--vel_scale", str(vel_scale),
        "--loop",
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: 可视化失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n用户中断")
        return False


def main():
    parser = argparse.ArgumentParser(description="批量可视化 npz 文件")
    parser.add_argument("directory", type=str, help="包含 npz 文件的目录")
    parser.add_argument("--robot_type", type=str, default="g1", 
                       choices=["g1", "t1", "adam_sp"],
                       help="机器人类型 (默认: g1)")
    parser.add_argument("--robot_urdf", type=str, default=None,
                       help="机器人 URDF 文件路径 (如果不指定，会根据 robot_type 自动选择)")
    parser.add_argument("--vel_scale", type=float, default=0.1,
                       help="速度箭头缩放比例 (默认: 0.1)")
    parser.add_argument("--pattern", type=str, default="*.npz",
                       help="文件匹配模式 (默认: *.npz)")
    
    args = parser.parse_args()
    
    # 如果没有指定 URDF 路径，根据机器人类型自动选择
    if args.robot_urdf is None:
        script_dir = Path(__file__).parent
        models_dir = script_dir.parent / "models"
        
        if args.robot_type == "g1":
            args.robot_urdf = str(models_dir / "g1" / "g1_29dof.urdf")
        elif args.robot_type == "t1":
            args.robot_urdf = str(models_dir / "t1" / "t1_29dof.urdf")
        elif args.robot_type == "adam_sp":
            args.robot_urdf = str(models_dir / "adam_sp" / "adam_sp.urdf")
    
    if not Path(args.robot_urdf).exists():
        print(f"错误: URDF 文件不存在: {args.robot_urdf}")
        sys.exit(1)
    
    # 查找所有 npz 文件
    npz_dir = Path(args.directory)
    npz_files = sorted(npz_dir.glob(args.pattern))
    
    if not npz_files:
        print(f"在 {args.directory} 中没有找到匹配 '{args.pattern}' 的文件")
        sys.exit(1)
    
    print(f"找到 {len(npz_files)} 个文件:")
    for i, npz_file in enumerate(npz_files, 1):
        print(f"  {i}. {npz_file.name}")
    
    print(f"\n机器人类型: {args.robot_type}")
    print(f"URDF 路径: {args.robot_urdf}")
    print(f"速度缩放: {args.vel_scale}")
    
    # 交互式选择要可视化的文件
    print("\n选项:")
    print("  输入文件编号来可视化单个文件")
    print("  输入 'all' 来依次可视化所有文件")
    print("  输入 'q' 退出")
    
    while True:
        choice = input("\n请选择: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'all':
            for npz_file in npz_files:
                success = visualize_npz(npz_file, args.robot_type, args.robot_urdf, args.vel_scale)
                if not success:
                    break
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(npz_files):
                    visualize_npz(npz_files[idx], args.robot_type, args.robot_urdf, args.vel_scale)
                else:
                    print(f"错误: 无效的编号。请输入 1-{len(npz_files)}")
            except ValueError:
                print("错误: 无效的输入")


if __name__ == "__main__":
    main()

