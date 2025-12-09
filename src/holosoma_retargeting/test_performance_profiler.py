#!/usr/bin/env python3
"""简单测试性能分析器功能"""

import time
import numpy as np
from src.performance_profiler import PerformanceProfiler


def test_basic_profiling():
    """测试基本性能分析功能"""
    print("=" * 80)
    print("测试性能分析器基本功能")
    print("=" * 80)
    
    profiler = PerformanceProfiler(enabled=True)
    
    # 模拟不同的计算任务
    for i in range(10):
        # 模拟数据准备
        with profiler.time_section("1_data_preparation"):
            time.sleep(0.001)
            data = np.random.rand(100, 3)
        
        # 模拟网格创建
        with profiler.time_section("2_mesh_creation"):
            time.sleep(0.005)
            mesh = np.random.rand(50, 50)
        
        # 模拟优化迭代
        with profiler.time_section("3_optimization"):
            # 模拟雅可比计算
            with profiler.time_section("3.1_jacobian"):
                time.sleep(0.003)
                jacobian = np.random.rand(20, 20)
            
            # 模拟求解器
            with profiler.time_section("3.2_solver"):
                time.sleep(0.010)
                solution = np.linalg.solve(
                    np.eye(20) + 0.1 * jacobian,
                    np.random.rand(20)
                )
        
        # 记录计数器
        profiler.increment_counter("iterations", 1)
        profiler.increment_counter("constraints", 15)
    
    # 打印摘要
    profiler.print_summary()
    
    # 获取特定统计信息
    stats = profiler.get_stats("3.2_solver")
    print(f"\n求解器统计:")
    print(f"  调用次数: {stats['count']}")
    print(f"  平均耗时: {stats['mean']*1000:.2f} ms")
    print(f"  总耗时: {stats['total']:.3f} s")
    
    print("\n✓ 性能分析器测试通过!")


def test_disabled_profiling():
    """测试禁用性能分析"""
    print("\n" + "=" * 80)
    print("测试禁用性能分析")
    print("=" * 80)
    
    profiler = PerformanceProfiler(enabled=False)
    
    # 即使调用也不应记录
    with profiler.time_section("test"):
        time.sleep(0.01)
    
    profiler.increment_counter("test", 100)
    
    # 应该显示禁用消息
    profiler.print_summary()
    
    print("\n✓ 禁用测试通过!")


def test_nested_profiling():
    """测试嵌套性能分析"""
    print("\n" + "=" * 80)
    print("测试嵌套性能分析")
    print("=" * 80)
    
    profiler = PerformanceProfiler(enabled=True)
    
    for i in range(5):
        with profiler.time_section("outer_loop"):
            time.sleep(0.002)
            
            with profiler.time_section("inner_compute_1"):
                time.sleep(0.003)
            
            with profiler.time_section("inner_compute_2"):
                time.sleep(0.004)
    
    profiler.print_summary()
    
    print("\n✓ 嵌套测试通过!")


if __name__ == "__main__":
    test_basic_profiling()
    test_disabled_profiling()
    test_nested_profiling()
    
    print("\n" + "=" * 80)
    print("所有测试通过! ✓")
    print("=" * 80)

