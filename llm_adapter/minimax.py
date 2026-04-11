#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax 大模型适配器
"""

import os
import json
from typing import Optional
import requests

from .base import LLMAdapter, LLMResponse, CompletionRequest


class MiniMaxAdapter(LLMAdapter):
    """
    MiniMax 大模型适配
    支持 MiniMax-M2.7 等模型
    """
    
    DEFAULT_API_BASE = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        group_id: Optional[str] = None,
        model_name: str = "mini-max-latest",
        api_base: str = DEFAULT_API_BASE,
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.group_id = group_id or os.getenv("MINIMAX_GROUP_ID", "")
        self.model_name = model_name
        self.api_base = api_base
    
    def is_configured(self) -> bool:
        """检查是否配置正确"""
        return bool(self.api_key and self.group_id)
    
    def complete(self, request: CompletionRequest) -> LLMResponse:
        """调用 MiniMax 补全"""
        if not self.is_configured():
            return LLMResponse(
                success=False,
                content="",
                error="MINIMAX_API_KEY or MINIMAX_GROUP_ID not configured",
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = [
            {"role": "user", "content": request.prompt},
        ]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        try:
            response = requests.post(
                f"{self.api_base}?GroupId={self.group_id}",
                headers=headers,
                json=payload,
                timeout=120,
            )
            
            if response.status_code != 200:
                return LLMResponse(
                    success=False,
                    content="",
                    error=f"HTTP {response.status_code}: {response.text}",
                )
            
            data = response.json()
            if data.get("code") != 0:
                return LLMResponse(
                    success=False,
                    content="",
                    error=f"API error: {data.get('message', 'unknown')}",
                )
            
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            return LLMResponse(
                success=True,
                content=content,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
            
        except Exception as e:
            return LLMResponse(
                success=False,
                content="",
                error=str(e),
            )
