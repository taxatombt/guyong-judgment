#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goal_system.py — 目标系统 最小可用版

五级拆解结构：
  五年目标 → 年度目标 → 月度里程碑 → 本周任务 → 今日优先级

核心输出：给好奇心引擎提供对齐得分，影响优先级排序

核心问题：**我的五年方向是什么？当前任务对齐吗？**
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

# 文件路径
GOALS_FILE = Path(__file__).parent.parent / "goal_system" / "goals.json"


@dataclass
class FiveYearGoal:
    """五年目标"""
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class AnnualGoal:
    """年度目标"""
    description: str
    keywords: List[str] = field(default_factory=list)
    progress: int = 0  # 0-100


@dataclass
class MonthlyMilestone:
    """月度里程碑"""
    description: str
    completed: bool = False


@dataclass
class WeeklyTask:
    """本周任务"""
    description: str
    completed: bool = False


@dataclass
class DailyPriority:
    """今日优先级"""
    description: str
    priority: int  # 1-5


@dataclass
class GoalSystem:
    """目标系统主类"""
    five_year: FiveYearGoal = None
    annual: AnnualGoal = None
    monthly: List[MonthlyMilestone] = field(default_factory=list)
    weekly: List[WeeklyTask] = field(default_factory=list)
    daily: List[DailyPriority] = field(default_factory=list)

    @classmethod
    def load_from_file(cls, path: Path = None) -> "GoalSystem":
        """从文件加载目标"""
        if path is None:
            path = GOALS_FILE
        
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        gs = cls()
        gs.five_year = FiveYearGoal(**data.get("five_year", {}))
        gs.annual = AnnualGoal(**data.get("annual", {}))
        gs.monthly = [MonthlyMilestone(**m) for m in data.get("monthly", [])]
        gs.weekly = [WeeklyTask(**t) for t in data.get("weekly", [])]
        gs.daily = [DailyPriority(**p) for p in data.get("daily", [])]
        return gs

    def save_to_file(self, path: Path = None):
        """保存到文件"""
        if path is None:
            path = GOALS_FILE
        
        data = {
            "five_year": {
                "description": self.five_year.description,
                "keywords": self.five_year.keywords,
            },
            "annual": {
                "description": self.annual.description,
                "keywords": self.annual.keywords,
                "progress": self.annual.progress,
            },
            "monthly": [
                {"description": m.description, "completed": m.completed}
                for m in self.monthly
            ],
            "weekly": [
                {"description": t.description, "completed": t.completed}
                for t in self.weekly
            ],
            "daily": [
                {"description": p.description, "priority": p.priority}
                for p in self.daily
            ],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def calculate_alignment_score(self, topic: str) -> float:
        """
        计算话题和长期目标的对齐得分（0-1）
        越高越值得探索
        """
        score = 0.0
        topic_lower = topic.lower()

        # 五年目标关键词匹配（权重最高）
        for kw in self.five_year.keywords:
            if kw.lower() in topic_lower:
                score += 0.5
                break  # 匹配到就给满分

        # 年度目标关键词匹配
        for kw in self.annual.keywords:
            if kw.lower() in topic_lower:
                score += 0.3
                break

        # 检查月度/本周是否在做相关事情
        for m in self.monthly:
            if not m.completed and m.description.lower() in topic_lower:
                score += 0.15
                break

        return min(score, 1.0)

    def get_daily_priorities(self) -> List[DailyPriority]:
        """获取今日优先级排序"""
        return sorted(self.daily, key=lambda x: -x.priority)

    def mark_weekly_completed(self, index: int) -> bool:
        """标记周任务完成"""
        if 0 <= index < len(self.weekly):
            self.weekly[index].completed = True
            self.save_to_file()
            return True
        return False

    def format_goals(self) -> str:
        """格式化输出目标结构，人类可读"""
        lines = ["=== 目标系统 ===\n"]

        lines.append(f"📌 五年目标：{self.five_year.description}")
        if self.five_year.keywords:
            lines.append(f"关键词：{', '.join(self.five_year.keywords)}\n")

        lines.append(f"🎯 年度目标：{self.annual.description}")
        lines.append(f"进度：{self.annual.progress}%")
        if self.annual.keywords:
            lines.append(f"关键词：{', '.join(self.annual.keywords)}\n")

        if self.monthly:
            lines.append("🗓️  月度里程碑：")
            for idx, m in enumerate(self.monthly, 1):
                check = "✅" if m.completed else "⬜"
                lines.append(f"  {check} {idx}. {m.description}")
            lines.append("")

        if self.weekly:
            lines.append("📋 本周任务：")
            for idx, t in enumerate(self.weekly, 1):
                check = "✅" if t.completed else "⬜"
                lines.append(f"  {check} {idx}. {t.description}")
            lines.append("")

        if self.daily:
            lines.append("🔝 今日优先级：")
            daily_sorted = self.get_daily_priorities()
            for idx, p in enumerate(daily_sorted, 1):
                stars = "⭐" * p.priority
                lines.append(f"  {stars} {idx}. {p.description}")

        return "\n".join(lines)


# 单例
_goal_system_instance = None


def get_goal_system() -> GoalSystem:
    """获取目标系统单例"""
    global _goal_system_instance
    if _goal_system_instance is None:
        _goal_system_instance = GoalSystem.load_from_file()
    return _goal_system_instance


if __name__ == "__main__":
    gs = get_goal_system()
    print(gs.format_goals())
