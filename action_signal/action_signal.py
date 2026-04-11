#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
action_signal — 聚活标准化行动信号生成和格式化

核心功能：
- 从行动规划生成标准化行动信号
- 格式化输出给机器人（JSON格式，机器可直接解析）
- 验证信号合法性
- 文件持久化存储
"""

import json
import uuid
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import asdict

from .types import (
    ActionTypeEnum,
    ActionType,
    ActionSignal,
    ActionSignalList,
)

from action_system.action_system import NextAction, ActionPlan


def generate_action_signals(
    action_plan: ActionPlan,
    session_id: str,
) -> ActionSignalList:
    """
    从行动规划生成标准化行动信号列表
    
    Args:
        action_plan: 来自 action_system 的行动规划
        session_id: 当前会话ID
        
    Returns:
        排序好的行动信号列表（优先级从高到低）
    """
    signals: ActionSignalList = []
    
    for item in action_plan.items:
        signal = ActionSignal(
            action_id=str(uuid.uuid4())[:8],
            session_id=session_id,
            action_type=_map_quadrant_to_type(item.quadrant),
            content=item.description,
            priority=item.pressure_score // 10,  # pressure_score 0-500 → 0-5
            deadline=str(item.deadline) if item.deadline else None,
            metadata={
                "quadrant": item.quadrant,
                "pressure_score": item.pressure_score,
                "importance": item.importance,
                "original_action_id": item.action_id,
            },
        )
        signals.append(signal)
    
    # 按优先级降序排序
    signals.sort(key=lambda s: -s.priority)
    return signals


def _map_quadrant_to_type(quadrant: str) -> ActionTypeEnum:
    """
    内部：将四象限分类映射到行动类型
    """
    mapping = {
        "important_urgent": ActionTypeEnum.SPEAK,  # 重要紧急一般是立即回复
        "important_not_urgent": ActionTypeEnum.SPEAK,
        "unimportant_urgent": ActionTypeEnum.RUN_COMMAND,
        "unimportant_not_urgent": ActionTypeEnum.SPEAK,
    }
    return mapping.get(quadrant, ActionTypeEnum.CUSTOM)


def format_for_robot(signals: ActionSignalList) -> str:
    """
    格式化输出给机器人 — JSON数组格式，机器直接JSON.loads就能用
    
    Args:
        signals: 行动信号列表
        
    Returns:
        JSON字符串，机器人可直接解析
    """
    data = [s.to_dict() for s in signals]
    return json.dumps(data, ensure_ascii=False, indent=2)


def validate_signal(signal: ActionSignal) -> tuple[bool, str]:
    """
    验证行动信号是否合法
    
    Returns:
        (is_valid, error_message)
    """
    if not signal.action_id:
        return False, "action_id is required"
    if not signal.session_id:
        return False, "session_id is required"
    if not signal.content:
        return False, "content is required"
    if signal.priority < 1 or signal.priority > 5:
        return False, f"priority must be 1-5, got {signal.priority}"
    return True, ""


def save_to_file(signals: ActionSignalList, filepath: str) -> None:
    """
    保存行动信号到JSON文件
    
    Args:
        signals: 行动信号列表
        filepath: 输出文件路径
    """
    data = [s.to_dict() for s in signals]
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_file(filepath: str) -> ActionSignalList:
    """
    从JSON文件加载行动信号
    
    Args:
        filepath: 输入文件路径
        
    Returns:
        行动信号列表
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    signals: ActionSignalList = []
    for item in data:
        signals.append(ActionSignal.from_dict(item))
    return signals
