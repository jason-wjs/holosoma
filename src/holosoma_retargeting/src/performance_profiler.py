"""Performance profiling utilities for retargeting."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

import numpy as np


class PerformanceProfiler:
    """性能分析器，用于跟踪各个计算步骤的耗时。"""

    def __init__(self, enabled: bool = True):
        """初始化性能分析器。
        
        Args:
            enabled: 是否启用性能分析
        """
        self.enabled = enabled
        self.timings: dict[str, list[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)
        self.section_stack: list[tuple[str, float]] = []

    def time_section(self, name: str):
        """创建一个计时上下文管理器。
        
        Args:
            name: 计时段落的名称
            
        Returns:
            上下文管理器
        """
        return self._TimerContext(self, name)

    def increment_counter(self, name: str, value: int = 1):
        """增加计数器。
        
        Args:
            name: 计数器名称
            value: 增加的值
        """
        if self.enabled:
            self.counters[name] += value

    def record_value(self, name: str, value: float):
        """记录一个值。
        
        Args:
            name: 值的名称
            value: 要记录的值
        """
        if self.enabled:
            self.timings[name].append(value)

    def print_summary(self, top_n: int = 20):
        """打印性能分析摘要。
        
        Args:
            top_n: 显示耗时最多的前 N 项
        """
        if not self.enabled:
            print("Performance profiling is disabled.")
            return

        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY".center(80))
        print("=" * 80)

        if self.timings:
            # 按总耗时排序
            sorted_timings = sorted(
                self.timings.items(),
                key=lambda x: sum(x[1]),
                reverse=True
            )[:top_n]

            print(f"\n{'Section':<40} {'Calls':<8} {'Total (s)':<12} {'Avg (ms)':<12} {'%':<8}")
            print("-" * 80)

            total_time = sum(sum(times) for times in self.timings.values())

            for name, times in sorted_timings:
                total = sum(times)
                avg = np.mean(times) * 1000  # 转换为毫秒
                count = len(times)
                percentage = (total / total_time * 100) if total_time > 0 else 0

                print(f"{name:<40} {count:<8} {total:<12.3f} {avg:<12.2f} {percentage:<8.1f}")

            print("-" * 80)
            print(f"{'Total Time':<40} {'':<8} {total_time:<12.3f}")

        if self.counters:
            print("\n" + "=" * 80)
            print("COUNTERS".center(80))
            print("=" * 80)
            print(f"\n{'Counter':<50} {'Count':<15}")
            print("-" * 80)

            for name, count in sorted(self.counters.items()):
                print(f"{name:<50} {count:<15}")

        print("\n" + "=" * 80)

    def get_stats(self, name: str) -> dict[str, Any]:
        """获取指定段落的统计信息。
        
        Args:
            name: 段落名称
            
        Returns:
            包含统计信息的字典
        """
        if name not in self.timings or not self.timings[name]:
            return {}

        times = self.timings[name]
        return {
            "count": len(times),
            "total": sum(times),
            "mean": np.mean(times),
            "std": np.std(times),
            "min": min(times),
            "max": max(times),
        }

    def reset(self):
        """重置所有计时器和计数器。"""
        self.timings.clear()
        self.counters.clear()
        self.section_stack.clear()

    class _TimerContext:
        """计时器上下文管理器。"""

        def __init__(self, profiler: PerformanceProfiler, name: str):
            self.profiler = profiler
            self.name = name
            self.start_time = 0.0

        def __enter__(self):
            if self.profiler.enabled:
                self.start_time = time.perf_counter()
                self.profiler.section_stack.append((self.name, self.start_time))
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.profiler.enabled:
                elapsed = time.perf_counter() - self.start_time
                self.profiler.timings[self.name].append(elapsed)
                if self.profiler.section_stack:
                    self.profiler.section_stack.pop()


# 全局实例，可选使用
_global_profiler: PerformanceProfiler | None = None


def get_global_profiler() -> PerformanceProfiler:
    """获取全局性能分析器实例。"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def enable_profiling():
    """启用全局性能分析。"""
    get_global_profiler().enabled = True


def disable_profiling():
    """禁用全局性能分析。"""
    get_global_profiler().enabled = False


def print_global_summary():
    """打印全局性能分析摘要。"""
    get_global_profiler().print_summary()

