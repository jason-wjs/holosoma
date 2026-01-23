#!/usr/bin/env python3
"""批量转换重定向后的数据为 PBHC 格式。

支持的数据格式: bvh, smplh, mocap, lafan

PBHC 格式包含:
- fps: 帧率
- base_position: 基座位置 (N, 3)
- base_orientation: 基座方向四元数 (N, 4) [w, x, y, z]
- joint_position: 关节位置 (N, num_joints)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="批量转换重定向数据为 PBHC 格式")
    parser.add_argument(
        "--source-dir",
        type=str,
        required=True,
        help="源数据目录（包含 .npz 文件）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="输出目录",
    )
    parser.add_argument(
        "--robot",
        type=str,
        default="adam_sp",
        choices=["adam_sp", "g1", "t1"],
        help="机器人类型 (默认: adam_sp)",
    )
    parser.add_argument(
        "--data-format",
        type=str,
        default="smplh",
        choices=["bvh", "smplh", "mocap", "lafan"],
        help="数据格式 (默认: smplh)",
    )
    parser.add_argument(
        "--robot-xml-path",
        type=str,
        default=None,
        help="机器人 XML 路径（可选，默认自动推断）",
    )
    parser.add_argument(
        "--input-fps",
        type=int,
        default=30,
        help="输入帧率 (默认: 30)",
    )
    parser.add_argument(
        "--output-fps",
        type=int,
        default=30,
        help="输出帧率 (默认: 30)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.npz",
        help="文件匹配模式 (默认: *.npz)",
    )
    
    args = parser.parse_args()
    
    # 设置路径
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    
    if not source_dir.exists():
        print(f"错误: 源目录不存在: {source_dir}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置机器人 XML 路径
    if args.robot_xml_path is None:
        robot_xml_path = f"models/{args.robot}/{args.robot}_29dof.xml"
    else:
        robot_xml_path = args.robot_xml_path
    
    # 查找所有匹配的文件
    input_files = list(source_dir.glob(args.pattern))
    
    if not input_files:
        print(f"错误: 未找到匹配的文件: {source_dir}/{args.pattern}")
        sys.exit(1)
    
    print("=" * 60)
    print("批量转换 PBHC 格式")
    print("=" * 60)
    print(f"源目录: {source_dir}")
    print(f"输出目录: {output_dir}")
    print(f"机器人类型: {args.robot}")
    print(f"数据格式: {args.data_format}")
    print(f"机器人 XML: {robot_xml_path}")
    print(f"输入帧率: {args.input_fps}")
    print(f"输出帧率: {args.output_fps}")
    print(f"找到文件: {len(input_files)} 个")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, input_file in enumerate(input_files, 1):
        # 生成输出文件名
        output_file = output_dir / f"{input_file.stem}_pbhc.npz"
        
        print(f"\n[{i}/{len(input_files)}] 处理: {input_file.name}")
        print(f"  输入: {input_file}")
        print(f"  输出: {output_file}")
        
        # 构建转换命令
        cmd = [
            "python",
            "data_conversion/convert_data_format_mj.py",
            "--input-file", str(input_file),
            "--output-name", str(output_file),
            "--data-format", args.data_format,
            "--robot", args.robot,
            "--robot-xml-path", robot_xml_path,
            "--object-name", "ground",
            "--output-format", "pbhc",
            "--input-fps", str(args.input_fps),
            "--output-fps", str(args.output_fps),
            "--headless",
            "--once",
        ]
        
        try:
            # 运行转换命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("  ✓ 转换成功")
                success_count += 1
            else:
                print("  ✗ 转换失败")
                print(f"  错误信息: {result.stderr}")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print("  ✗ 转换超时")
            fail_count += 1
        except Exception as e:
            print(f"  ✗ 转换出错: {e}")
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("转换完成")
    print("=" * 60)
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    print(f"总计: {len(input_files)} 个文件")
    print("=" * 60)
    
    # 如果有失败的文件，返回非零退出码
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

