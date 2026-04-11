#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
confidence.py — 置信度计算模块

核心功能：
- 每个维度计算判断的置信度
- 综合平均置信度
- 低置信度触发好奇心探索
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DimensionConfidence:
    dim_id: str
    confidence: float  # 0-1
    reason: str


def calculate_dimension_confidence(dim_id: str, answers: Dict) -> float:
    """计算单个维度的置信度"""
    # 默认中等置信度
    base_confidence = 0.5
    
    # 维度特定规则
    dimension_rules = {
        "cognitive": {
            "keywords": ["直觉", "感觉", "分析", "思考", "认知", "偏差", "假设", "事实"],
            "has_keywords": 0.2,
        },
        "game_theory": {
            "keywords": ["玩家", "诉求", "策略", "均衡", "激励", "第三方"],
            "has_keywords": 0.25,
        },
        "economic": {
            "keywords": ["机会成本", "边际", "代价", "收益", "成本", "不可逆"],
            "has_keywords": 0.25,
        },
        "dialectical": {
            "keywords": ["矛盾", "主要", "次要", "实际", "现实", "对立", "变化"],
            "has_keywords": 0.25,
        },
        "emotional": {
            "keywords": ["情绪", "感受", "信号", "焦虑", "兴奋", "直觉"],
            "has_keywords": 0.2,
        },
        "intuitive": {
            "keywords": ["第一反应", "身体", "直觉", "经验", "模式"],
            "has_keywords": 0.2,
        },
        "moral": {
            "keywords": ["应该", "原则", "公正", "价值", "伦理", "底线"],
            "has_keywords": 0.25,
        },
        "social": {
            "keywords": ["群体", "压力", "身份", "认同", "社会", "独立"],
            "has_keywords": 0.2,
        },
        "temporal": {
            "keywords": ["长期", "短期", "五年", "复利", "折扣", "未来"],
            "has_keywords": 0.2,
        },
        "metacognitive": {
            "keywords": ["思考", "校准", "信心", "盲区", "反对", "元认知"],
            "has_keywords": 0.2,
        },
    }
    
    if dim_id not in dimension_rules:
        return base_confidence
    
    # 如果有回答，置信度提升
    if dim_id in answers and answers[dim_id]:
        answer_text = str(answers[dim_id])
        rules = dimension_rules[dim_id]
        for kw in rules["keywords"]:
            if kw in answer_text:
                base_confidence += rules["has_keywords"]
                break
    
    return min(1.0, max(0.0, base_confidence))


def calculate_average_confidence(dim_confidence: Dict[str, float]) -> float:
    """计算平均置信度"""
    if not dim_confidence:
        return 0.5
    total = sum(dim_confidence.values())
    return total / len(dim_confidence)


def get_low_confidence_dimensions(dim_confidence: Dict[str, float], threshold: float = 0.5) -> List[str]:
    """返回低置信度的维度"""
    return [dim for dim, conf in dim_confidence.items() if conf < threshold]
