#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
action_signal — 聚活标准化行动信号输出模块

核心功能：
- 定义机器可解析的标准化行动信号格式
- 输出给机器人/执行器，指导机器人工作
- 支持自定义参数，适配不同机器人
"""

from .action_signal import (
    ActionSignal,
    ActionType,
    ActionSignalList,
    generate_action_signals,
    format_for_robot,
    save_to_file,
    load_from_file,
    validate_signal,
)

from .types import (
    ActionTypeEnum,
)

__all__ = [
    # Types
    'ActionTypeEnum',
    'ActionType',
    'ActionSignal',
    'ActionSignalList',
    # Functions
    'generate_action_signals',
    'format_for_robot',
    'save_to_file',
    'load_from_file',
    'validate_signal',
]
