#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_adapter config — 配置加载，根据环境变量获取适配器
"""

import os
from typing import Optional

from .base import LLMAdapter
from .minimax import MiniMaxAdapter
from .openai import OpenAIAdapter
from .ollama import OllamaAdapter


def load_config() -> dict:
    """
    从环境变量加载配置
    也可以从配置文件读取，这里优先环境变量
    """
    return {
        "provider": os.getenv("JUHUO_LLM_PROVIDER", "minimax"),  # minimax / openai / ollama
        "minimax_api_key": os.getenv("MINIMAX_API_KEY", ""),
        "minimax_group_id": os.getenv("MINIMAX_GROUP_ID", ""),
        "minimax_model": os.getenv("MINIMAX_MODEL", "mini-max-latest"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "openai_api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3:8b"),
        "ollama_api_base": os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
    }


def get_adapter() -> Optional[LLMAdapter]:
    """
    根据配置获取适配器
    返回 None 表示没有配置好
    """
    config = load_config()
    provider = config["provider"]
    
    if provider == "minimax":
        adapter = MiniMaxAdapter(
            api_key=config["minimax_api_key"],
            group_id=config["minimax_group_id"],
            model_name=config["minimax_model"],
        )
        if adapter.is_configured():
            return adapter
    
    elif provider == "openai":
        adapter = OpenAIAdapter(
            api_key=config["openai_api_key"],
            model_name=config["openai_model"],
            api_base=config["openai_api_base"],
        )
        if adapter.is_configured():
            return adapter
    
    elif provider == "ollama":
        adapter = OllamaAdapter(
            model_name=config["ollama_model"],
            api_base=config["ollama_api_base"],
        )
        if adapter.is_configured():
            return adapter
    
    return None
