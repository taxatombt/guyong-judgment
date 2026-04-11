#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
curiosity_engine — 聚活好奇心引擎

独特核心技术：
- 锁定兴趣域：只探索你真正感兴趣的方向，不浪费认知资源
- 双随机游走：80%目标导向，20%自由随机探索，平衡功利和创造力
"""

from .curiosity_engine import (
    CuriosityItem,
    TriggerInfo,
    CuriosityEngine,
    trigger_from_low_confidence,
    trigger_from_causal_mismatch,
    get_top_open,
    resolve,
    get_daily_list,
    full_report,
)

__all__ = [
    "CuriosityItem",
    "TriggerInfo",
    "CuriosityEngine",
    "trigger_from_low_confidence",
    "trigger_from_causal_mismatch",
    "get_top_open",
    "resolve",
    "get_daily_list",
    "full_report",
]
