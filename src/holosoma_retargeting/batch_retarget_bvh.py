#!/usr/bin/env python3
"""
批量处理 converted_bvh 文件夹中的所有 BVH 文件
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 设置基本参数
DATA_PATH = Path("demo_data/converted_bvh")
SAVE_DIR = Path("demo_results/adam_sp/robot_only/converted_bvh")
ROBOT = "adam_sp"
DATA_FORMAT = "bvh"

# 重定向参数
N_FIRST_ITER = 25
N_SUBSEQUENT_ITER = 1
SMOOTH_WEIGHT = 0.3
STEP_SIZE = 1.0

# 是否启用可视化（批量处理时建议关闭）
ENABLE_VISUALIZE = True
ENABLE_DEBUG = True

def main():
    # 检查数据路径是否存在
    if not DATA_PATH.exists():
        print(f"错误: 数据路径不存在: {DATA_PATH}")
        sys.exit(1)
    
    # 创建保存目录
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 查找所有 BVH 文件
    bvh_files = sorted(list(DATA_PATH.glob("*.bvh")))
    
    if not bvh_files:
        print(f"错误: 在 {DATA_PATH} 中未找到 BVH 文件")
        sys.exit(1)
    
    print("=" * 60)
    print("开始批量处理 BVH 文件")
    print(f"数据路径: {DATA_PATH}")
    print(f"保存路径: {SAVE_DIR}")
    print(f"找到 {len(bvh_files)} 个 BVH 文件")
    print("=" * 60)
    print()
    
    # 统计信息
    total = len(bvh_files)
    success = 0
    failed = 0
    failed_files = []
    
    # 开始时间
    start_time = datetime.now()
    
    # 遍历所有 BVH 文件
    for idx, bvh_file in enumerate(bvh_files, 1):
        # 获取文件名（不含扩展名）
        task_name = bvh_file.stem
        
        print("-" * 60)
        print(f"[{idx}/{total}] 处理文件: {task_name}")
        print("-" * 60)
        
        # 构建命令
        cmd = [
            "python", "examples/robot_retarget.py",
            "--data_path", str(DATA_PATH),
            "--task-type", "robot_only",
            "--task-name", task_name,
            "--data_format", DATA_FORMAT,
            "--robot", ROBOT,
            "--save_dir", str(SAVE_DIR),
            "--retargeter.n-first-iter", str(N_FIRST_ITER),
            "--retargeter.n-subsequent-iter", str(N_SUBSEQUENT_ITER),
            "--retargeter.smooth-weight", str(SMOOTH_WEIGHT),
            "--retargeter.step-size", str(STEP_SIZE),
            "--retargeter.no-activate-foot-sticking",
        ]
        
        # 可选参数
        if ENABLE_DEBUG:
            cmd.append("--retargeter.debug")
        if ENABLE_VISUALIZE:
            cmd.append("--retargeter.visualize")
        
        # 运行命令
        try:
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent,
                check=True,
                capture_output=False,  # 显示实时输出
            )
            success += 1
            print(f"✓ 成功处理: {task_name}")
        except subprocess.CalledProcessError as e:
            failed += 1
            failed_files.append(task_name)
            print(f"✗ 处理失败: {task_name} (退出码: {e.returncode})")
        except KeyboardInterrupt:
            print("\n\n用户中断处理")
            break
        except Exception as e:
            failed += 1
            failed_files.append(task_name)
            print(f"✗ 处理出错: {task_name} (错误: {str(e)})")
        
        print()
    
    # 结束时间
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 打印总结
    print("=" * 60)
    print("批量处理完成")
    print("=" * 60)
    print(f"总计: {total} 个文件")
    print(f"成功: {success} 个")
    print(f"失败: {failed} 个")
    print(f"耗时: {duration}")
    
    if failed_files:
        print("\n失败的文件列表:")
        for f in failed_files:
            print(f"  - {f}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

