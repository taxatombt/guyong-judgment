#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_system — 聚活个人对话聊天系统

核心功能：
- 完整对话历史持久化（全文件存储）
- 自动分析对话，触发相应功能模块
- 定时自动进化（基于对话记录生成进化建议）
- 固定单用户使用，身份特质完全锁定
"""

from .chat_system import (
    ChatMessage,
    ChatSession,
    ChatSystem,
    load_chat_system,
    get_current_session,
    auto_trigger_functions,
    save_dialogue_to_file,
    list_sessions,
)

__all__ = [
    'ChatMessage',
    'ChatSession',
    'ChatSystem',
    'load_chat_system',
    'get_current_session',
    'auto_trigger_functions',
    'save_dialogue_to_file',
    'list_sessions',
]
