#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
attention_filter.py — 注意力过滤器（信息接收系统核心）

定义：谷翔宇主动关注什么、被动接收什么、对什么信息敏感、忽略什么。
遵循底座顺序：信息接收 → 判断 → 因果记忆 → 自我模型

结构：
- 主动关注列表：按领域分类的关键词/来源
- 被动接收规则：哪些渠道一定看、哪些渠道过滤
- 紧急分流规则：什么级别的信息会打断当前工作
- 相似度匹配：过滤重复/相似信息
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import difflib


@dataclass
class AttentionItem:
    """一个关注项"""
    keyword: str
    category: str  # project / person / event / keyword
    priority: int   # 1-5, 5最高
    active: bool = True
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class IncomingMessage:
    """一条输入信息"""
    content: str
    source: str        # qq / email / calendar / github / system
    sender: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FilterResult:
    """过滤结果"""
    passed: bool
    priority: int  # 0-5, 0=丢弃
    reason: str
    matched_keywords: List[str] = field(default_factory=list)


class AttentionFilter:
    """谷翔宇的注意力过滤器"""

    def __init__(self):
        self.active_filters: List[AttentionItem] = []
        self._init_default_filters()

    def _init_default_filters(self):
        """初始化谷翔宇默认关注列表"""
        # 项目类（最高优先级）
        defaults = [
            # 自身项目
            ("guyong-juhuo", "project", 5),
            ("guyong-judgment", "project", 5),
            ("CoPaw", "project", 4),
            ("OpenClaw", "project", 4),
            ("QClaw", "project", 4),
            # 外部关注项目
            ("Sonagazi", "project", 4),
            ("MAGMA", "project", 3),
            ("DeerFlow", "project", 3),
            ("Claude Code", "project", 3),
            # 领域关键词
            ("AI Agent", "keyword", 3),
            ("因果记忆", "keyword", 4),
            ("数字永生", "keyword", 5),
            ("十维判断", "keyword", 4),
            ("超越人类", "keyword", 5),
            # 人际
            ("顾庸", "person", 5),
            ("谷翔宇", "person", 5),
        ]

        for kw, cat, prio in defaults:
            self.add_filter(kw, cat, prio)

    def add_filter(self, keyword: str, category: str, priority: int) -> AttentionItem:
        """添加一个关注项"""
        item = AttentionItem(keyword=keyword, category=category, priority=priority)
        self.active_filters.append(item)
        self.active_filters.sort(key=lambda x: x.priority, reverse=True)
        return item

    def remove_filter(self, keyword: str) -> bool:
        """移除一个关注项"""
        original_len = len(self.active_filters)
        self.active_filters = [f for f in self.active_filters if f.keyword != keyword]
        return len(self.active_filters) < original_len

    def filter(self, message: IncomingMessage) -> FilterResult:
        """
        过滤一条输入信息：
        返回是否通过，优先级多少
        """
        # 规则1：渠道优先级
        channel_priority = {
            "qq": 3,
            "system": 4,
            "email": 2,
            "calendar": 3,
            "github": 2,
            "news": 1,
        }
        base_prio = channel_priority.get(message.source, 1)

        # 规则2：关键词匹配
        matched = []
        max_prio = base_prio
        content_lower = message.content.lower()

        for item in self.active_filters:
            if item.keyword.lower() in content_lower:
                matched.append(item.keyword)
                if item.priority > max_prio:
                    max_prio = item.priority

        # 规则3：紧急检测
        emergency_words = ["紧急", "救命", "危险", "生死", "法律", "犯罪"]
        for word in emergency_words:
            if word in message.content:
                max_prio = 5
                matched.append(word)

        # 规则4：噪音检测
        noise_words = ["营销", "广告", "抽奖", "红包", "点赞", "砍一刀"]
        for word in noise_words:
            if word in message.content:
                # 就算有匹配关键词，营销也降优先级
                max_prio = max(0, max_prio - 3)

        # 决策：优先级0 → 丢弃
        if max_prio <= 0:
            return FilterResult(
                passed=False,
                priority=0,
                reason="噪音过滤",
                matched_keywords=matched
            )

        # 去重：最近一周相同主题只提醒一次
        if not self._is_recent_duplicate(message.content):
            pass

        return FilterResult(
            passed=True,
            priority=max_prio,
            reason=f"匹配{len(matched)}个关注项" if matched else "渠道默认通过",
            matched_keywords=matched
        )

    def _is_recent_duplicate(self, content: str, threshold: float = 0.7) -> bool:
        """检查最近一周是否有高度相似内容"""
        # TODO: 接入因果记忆的事件列表检查相似
        # 最小可用版先不做，只留接口
        return False

    def list_active(self) -> List[AttentionItem]:
        """列出所有活跃关注项"""
        return [f for f in self.active_filters if f.active]

    def get_by_category(self, category: str) -> List[AttentionItem]:
        """按分类获取关注项"""
        return [f for f in self.active_filters if f.category == category and f.active]


class InformationReceiver:
    """
    信息接收系统
    - 主动轮询关注来源
    - 被动接收推送
    - 走注意力过滤器
    - 输出给判断系统
    """

    def __init__(self):
        self.filter = AttentionFilter()
        self.received_history: List[Tuple[IncomingMessage, FilterResult]] = []

    def receive(self, message: IncomingMessage) -> FilterResult:
        """接收一条信息，过滤后返回结果"""
        result = self.filter.filter(message)
        self.received_history.append((message, result))
        return result

    def get_urgent_pending(self) -> List[IncomingMessage]:
        """获取优先级>=4的待处理信息"""
        urgent = []
        for msg, result in self.received_history:
            if result.passed and result.priority >= 4:
                urgent.append(msg)
        return urgent

    def export_filters(self) -> Dict:
        """导出过滤器配置"""
        return {
            "active_filters": [
                {"keyword": f.keyword, "category": f.category, "priority": f.priority}
                for f in self.filter.active_filters
            ]
        }


# 测试
if __name__ == "__main__":
    af = AttentionFilter()
    
    # 测试几个案例
    test_messages = [
        IncomingMessage(
            content="guyong-juhuo 因果记忆推送完成",
            source="system",
            sender="agent"
        ),
        IncomingMessage(
            content="这个营销红包点一下就能领",
            source="qq",
            sender="陌生人"
        ),
        IncomingMessage(
            content="今天帮用户修复了导入路径问题",
            source="github",
            sender="developer"
        ),
    ]
    
    print("=== AttentionFilter 测试 ===\n")
    for msg in test_messages:
        result = af.filter(msg)
        print(f"内容: {msg.content[:40]}...")
        print(f"  → passed={result.passed}, priority={result.priority}, reason={result.reason}")
        print()
