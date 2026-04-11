#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_model.py — 自我模型（底座生长第三层）

依赖：因果记忆 → 从历史判断中总结"我是谁"
- 统计各维度犯错频率
- 总结已知偏差
- 判断前自动提示盲区
- 持续进化：每次反馈后更新自我认知

核心问题：**我知道自己擅长什么、不擅长什么、什么时候会犯什么类型的错**
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from causal_memory.causal_memory import load_all_events, load_all_links


# 文件路径
SELF_MODEL_FILE = Path(__file__).parent.parent / "self_model.json"


@dataclass
class KnownBias:
    """已知偏差"""
    dimension: str          # 哪个维度
    mistake_count: int      # 失误次数
    first_seen: str
    last_seen: str
    description: str        # 描述："容易跳过这个维度" / "容易高估风险"
    confidence: float       # 0-1，我们有多确定这是真偏差

    def to_dict(self):
        return {
            "dimension": self.dimension,
            "mistake_count": self.mistake_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class Strength:
    """已知优势"""
    dimension: str
    correct_count: int
    last_used: str
    description: str


@dataclass
class SelfModel:
    """自我模型"""
    biases: Dict[str, KnownBias] = field(default_factory=dict)
    strengths: Dict[str, Strength] = field(default_factory=dict)
    total_decisions: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "biases": {k: v.to_dict() for k, v in self.biases.items()},
            "strengths": {k: v.to_dict() for k, v in self.strengths.items()},
            "total_decisions": self.total_decisions,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        model = cls()
        model.total_decisions = data.get("total_decisions", 0)
        model.updated_at = data.get("updated_at", datetime.now().isoformat())
        
        for dim, bias_data in data.get("biases", {}).items():
            model.biases[dim] = KnownBias(
                dimension=bias_data["dimension"],
                mistake_count=bias_data["mistake_count"],
                first_seen=bias_data["first_seen"],
                last_seen=bias_data["last_seen"],
                description=bias_data["description"],
                confidence=bias_data["confidence"],
            )
        
        for dim, strength_data in data.get("strengths", {}).items():
            model.strengths[dim] = Strength(
                dimension=strength_data["dimension"],
                correct_count=strength_data.get("correct_count", 0),
                last_used=strength_data.get("last_used", datetime.now().isoformat()),
                description=strength_data.get("description", ""),
            )
        
        return model


def init():
    """初始化自我模型文件"""
    if not SELF_MODEL_FILE.exists():
        empty_model = SelfModel()
        save_model(empty_model)


def save_model(model: SelfModel):
    """保存自我模型"""
    model.updated_at = datetime.now().isoformat()
    with open(SELF_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model.to_dict(), f, ensure_ascii=False, indent=2)


def load_model() -> SelfModel:
    """加载自我模型"""
    init()
    with open(SELF_MODEL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SelfModel.from_dict(data)


def update_from_feedback(event) -> Optional[KnownBias]:
    """
    从一次判断反馈更新自我模型
    event: 因果记忆事件（包含feedback）
    """
    model = load_model()
    model.total_decisions += 1

    # 如果反馈是坏的，记录偏差
    if event.get("feedback") in ["坏", "bad", "wrong"]:
        # 看哪些维度被跳过了 → 很可能跳过就是原因
        for dim in event.get("skipped", []):
            if dim in model.biases:
                b = model.biases[dim]
                b.mistake_count += 1
                b.last_seen = event["timestamp"]
                # 置信度随着次数增加
                b.confidence = min(1.0, b.confidence + 0.1)
            else:
                model.biases[dim] = KnownBias(
                    dimension=dim,
                    mistake_count=1,
                    first_seen=event["timestamp"],
                    last_seen=event["timestamp"],
                    description=f"容易跳过{dim}维度，导致判断失误",
                    confidence=0.3,  # 第一次就给0.3，次数多了置信度上升
                )
    
    # 如果反馈是好的，记录优势
    if event.get("feedback") in ["好", "good", "right"]:
        checked = event.get("must_check", []) + event.get("important", [])
        for dim in checked:
            if dim in model.strengths:
                s = model.strengths[dim]
                s.correct_count += 1
                s.last_used = event["timestamp"]
            else:
                model.strengths[dim] = Strength(
                    dimension=dim,
                    correct_count=1,
                    last_used=event["timestamp"],
                    description=f"在{dim}维度判断通常准确",
                )
    
    save_model(model)

    # 返回新增/更新的偏差
    if event.get("feedback") in ["坏", "bad", "wrong"] and event.get("skipped"):
        return model.biases[event["skipped"][0]]
    return None


def build_from_causal_memory():
    """
    从已有的因果记忆重建自我模型
    慢路径：每天跑一次，批量重建
    """
    events = load_all_events()
    model = SelfModel()
    
    for event in events:
        model.total_decisions += 1
        if event.get("feedback") in ["坏", "bad", "wrong"]:
            for dim in event.get("skipped", []):
                if dim in model.biases:
                    model.biases[dim].mistake_count += 1
                    model.biases[dim].last_seen = event["timestamp"]
                    model.biases[dim].confidence = min(1.0, model.biases[dim].confidence + 0.1)
                else:
                    model.biases[dim] = KnownBias(
                        dimension=dim,
                        mistake_count=1,
                        first_seen=event["timestamp"],
                        last_seen=event["timestamp"],
                        description=f"容易跳过{dim}维度，导致判断失误",
                        confidence=0.3,
                    )
        
        if event.get("feedback") in ["好", "good", "right"]:
            checked = event.get("must_check", []) + event.get("important", [])
            for dim in checked:
                if dim in model.strengths:
                    model.strengths[dim].correct_count += 1
                    model.strengths[dim].last_used = event["timestamp"]
                else:
                    model.strengths[dim] = Strength(
                        dimension=dim,
                        correct_count=1,
                        last_used=event["timestamp"],
                        description=f"在{dim}维度判断通常准确",
                    )
    
    save_model(model)
    return model


def get_self_warnings(current_result) -> Tuple[List[str], List[str]]:
    """
    给当前判断生成自我提醒：
    返回 (warnings, strengths)
    - warnings: "你过去在这些维度容易错，注意" + 带出因果历史前因后果
    - strengths: "你过去在这些维度做得好"
    """
    from causal_memory.causal_memory import find_similar_events
    
    model = load_model()
    warnings = []
    strengths = []

    # 检查当前跳过的维度有没有已知偏差
    for dim in current_result.get("skipped", []):
        if dim in model.biases:
            bias = model.biases[dim]
            warning_text = f"⚠️ 自我提醒：你过去有{bias.mistake_count}次跳过{dim}维度导致失误，这一次是否真的可以跳过？"
            
            # 打通因果记忆：找最近一次这个维度失误的案例，带进来
            similar_events = find_similar_events(dim, max_results=1)
            if similar_events:
                recent = similar_events[0]
                warning_text += f"\n    最近一次失误：{recent.get('task', '')[:80]}"
                if recent.get("feedback"):
                    warning_text += f" → 反馈: {recent['feedback']}"
            
            warnings.append(warning_text)
    
    # 检查当前检查的维度有没有已知优势
    checked = current_result.get("must_check", []) + current_result.get("important", [])
    for dim in checked:
        if dim in model.strengths:
            strength = model.strengths[dim]
            strengths.append(
                f"✓ 你过去在{dim}维度判断准确率不错，保持这个节奏"
            )
    
    return warnings, strengths


def format_self_report() -> str:
    """生成人类可读的自我模型报告"""
    model = load_model()
    lines = [f"自我模型报告 — 共 {model.total_decisions} 次决策记录\n"]

    lines.append("### 已知偏差（容易在这里犯错）")
    if model.biases:
        sorted_biases = sorted(model.biases.values(), key=lambda x: -x.mistake_count)
        for b in sorted_biases:
            lines.append(f"- {b.dimension}: {b.mistake_count} 次失误，置信度 {b.confidence:.1f} → {b.description}")
    else:
        lines.append("（还没有记录到偏差）")
    
    lines.append("\n### 已知优势（在这里做得不错）")
    if model.strengths:
        sorted_strengths = sorted(model.strengths.values(), key=lambda x: -x.correct_count)
        for s in sorted_strengths:
            lines.append(f"- {s.dimension}: {s.correct_count} 次正确 → {s.description}")
    else:
        lines.append("（还没有记录到优势）")
    
    lines.append(f"\n最后更新：{model.updated_at}")
    return "\n".join(lines)


# 测试
if __name__ == "__main__":
    init()
    model = load_model()
    print(format_self_report())
