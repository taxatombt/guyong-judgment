#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_adapter base — 大模型适配器基类

定义统一接口，不同大模型实现这个接口即可接入聚活
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class CompletionRequest:
    """统一补全请求"""
    prompt: str
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = False
    stop: Optional[List[str]] = None


@dataclass
class LLMResponse:
    """统一响应"""
    success: bool
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None


@dataclass
class KnowledgeUnit:
    """从文本提取的知识单元，用于OpenSpace进化"""
    name: str
    content: str
    category: str  # CORE_IDENTITY / SELF_MODEL / CAUSAL_MEMORY / JUDGMENT_RULE / GENERAL_SKILL
    confidence: float
    source: str  # 来源URL/文件/对话
    parent_skill_id: Optional[str] = None


class LLMAdapter(ABC):
    """大模型适配器抽象基类"""
    
    @abstractmethod
    def complete(self, request: CompletionRequest) -> LLMResponse:
        """文本补全"""
        pass
    
    def extract_knowledge(self, text: str, source: str) -> List[KnowledgeUnit]:
        """
        从长文本提取可进化知识单元
        默认实现用prompt提取，子类可以覆盖
        """
        prompt = f"""
从以下文本中提取可复用的知识单元，每个知识单元包含：
- name：知识名称（简洁）
- content：知识内容（完整）
- category：分类（可选值：CORE_IDENTITY / SELF_MODEL / CAUSAL_MEMORY / JUDGMENT_RULE / GENERAL_SKILL）
- confidence：你对这个知识的置信度 0-1

文本来源：{source}

文本内容：
{text[:8000]}

输出格式：JSON数组，每个元素是一个知识单元
        """.strip()
        
        response = self.complete(CompletionRequest(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
        ))
        
        if not response.success:
            return []
        
        # 尝试解析JSON
        import json
        try:
            # 查找JSON数组部分
            content = response.content
            start = content.find('[')
            end = content.rfind(']')
            if start >= 0 and end >= 0:
                content = content[start:end+1]
            data = json.loads(content)
            result = []
            for item in data:
                result.append(KnowledgeUnit(
                    name=item.get('name', 'unnamed'),
                    content=item.get('content', ''),
                    category=item.get('category', 'GENERAL_SKILL'),
                    confidence=float(item.get('confidence', 0.8)),
                    source=source,
                    parent_skill_id=item.get('parent_skill_id'),
                ))
            return result
        except:
            # 解析失败，返回整个文本作为一个知识单元
            return [KnowledgeUnit(
                name="extracted_text",
                content=response.content,
                category="GENERAL_SKILL",
                confidence=0.5,
                source=source,
            )]
    
    def suggest_evolution(self, current_content: str, execution_records: str) -> Optional[str]:
        """
        基于执行记录建议进化改进
        返回改进后的内容，如果无法建议返回None
        """
        prompt = f"""
当前技能内容：
{current_content}

近期执行记录和结果：
{execution_records}

请根据执行结果，改进这个技能内容，让它更准确。
只输出改进后的完整内容，不要其他解释。
        """.strip()
        
        response = self.complete(CompletionRequest(
            prompt=prompt,
            temperature=0.5,
            max_tokens=2000,
        ))
        
        if response.success and response.content.strip():
            return response.content.strip()
        return None
