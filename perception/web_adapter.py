#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_adapter.py — 网页提取适配器，对接 perception 注意力过滤

功能:
  1. 从 URL 提取结构化网页内容（用 extract-design）
  2. 分块分配优先级
  3. 输出给 AttentionFilter → 过滤后进入判断 pipeline

对接 guyong-juhuo 架构:
  URL → extract → structured blocks → priority → AttentionFilter → Judgment
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field

from perception.attention_filter import (
    AttentionFilter,
    IncomingMessage,
    FilterResult,
)


@dataclass
class WebBlock:
    """网页提取出的结构化块"""
    block_type: str  # title / heading / paragraph / list / code
    level: int        # 标题层级 1-6
    content: str     # 文本内容
    url: str         # 来源 URL
    priority: int = 0  # 计算出的优先级 0-5


@dataclass
class ExtractedWeb:
    """提取完成的完整网页"""
    url: str
    title: str
    blocks: List[WebBlock]
    metadata: Dict = field(default_factory=dict)


class WebExtractorAdapter:
    """
    网页提取适配器 → 对接 extract-design 输出 → 输出优先级排序块

    使用:
        adapter = WebExtractorAdapter()
        extracted = adapter.extract_from_url("https://...")
        filtered = adapter.filter_to_markdown(extracted, attention_filter)
    """

    def __init__(self):
        # 优先级基准
        self.base_priority = {
            "title":    5,  # 页面主标题
            "heading_1": 4, # H1
            "heading_2": 3, # H2
            "heading_3": 2, # H3
            "paragraph": 2, # 正文
            "list":       2, # 列表
            "code":       1, # 代码块
        }

    def extract_from_markdown(self, markdown_text: str, url: str, metadata: Optional[Dict] = None) -> ExtractedWeb:
        """
        从已经提取好的 markdown 解析结构化块
        (extract-design 输出 markdown，这里解析标题层级)
        """
        blocks = []
        lines = markdown_text.splitlines()
        title = ""

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # 检测标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                level = min(level, 6)
                content = line.lstrip('# ').strip()
                block_type = f"heading_{level}" if level > 1 else "title"
                if level == 1 and not title:
                    title = content
                blocks.append(WebBlock(
                    block_type=block_type,
                    level=level,
                    content=content,
                    url=url,
                ))
            # 检测列表
            elif line.startswith(('- ', '* ', '+ ', '1. ', '2. ')):
                blocks.append(WebBlock(
                    block_type="list",
                    level=0,
                    content=line,
                    url=url,
                ))
            # 检测代码块（围栏
            elif line.startswith('```'):
                continue  # skip fence markers
            elif line.startswith('    ') or line.startswith('`'):
                blocks.append(WebBlock(
                    block_type="code",
                    level=0,
                    content=line,
                    url=url,
                ))
            # 普通段落
            else:
                # 合并同段落
                if blocks and blocks[-1].block_type == "paragraph":
                    blocks[-1].content += "\n" + line
                else:
                    blocks.append(WebBlock(
                        block_type="paragraph",
                        level=0,
                        content=line,
                        url=url,
                    ))

        if not title and blocks:
                    first_heading = next((b for b in blocks if b.block_type.startswith("heading")), None)
                    if first_heading:
                        title = first_heading.content

        return ExtractedWeb(
            url=url,
            title=title,
            blocks=blocks,
            metadata=metadata or {},
        )

    def assign_priority(
        self,
        extracted: ExtractedWeb,
        attention_filter: AttentionFilter,
    ) -> ExtractedWeb:
        """
        为每个块分配优先级：
        - 基础优先级按块类型
        - 关键词匹配 attention_filter 提升优先级
        """
        for block in extracted.blocks:
            # 基础优先级
            base = self.base_priority.get(block.block_type, 1)
            block.priority = base

            # 用 attention_filter 关键词匹配加分
            msg = IncomingMessage(
                content=block.content,
                source="web",
                sender="extractor",
            )
            result = attention_filter.filter(msg)
            if result.passed and result.priority > block.priority:
                block.priority = result.priority

        # 按优先级降序排序（高优先级在前）
        extracted.blocks.sort(key=lambda b: -b.priority)

        return extracted

    def filter_to_markdown(
        self,
        extracted: ExtractedWeb,
        attention_filter: AttentionFilter,
        min_priority: int = 1,
        max_tokens: int = 16000,
    ) -> str:
        """
        过滤并输出 markdown，适合输入判断层
        - 只保留优先级 >= min_priority
        - 截断到 max_tokens 以内（高优先级优先保留）
        """
        extracted = self.assign_priority(extracted, attention_filter)

        lines = []
        lines.append(f"# Web: {extracted.title}\n")
        lines.append(f"URL: {extracted.url}\n\n")

        tokens_used = 0
        included = 0

        for block in extracted.blocks:
            if block.priority < min_priority:
                continue

            # 粗略 token 计算：4字符 = 1 token
            block_tokens = len(block.content) // 4
            if tokens_used + block_tokens > max_tokens:
                break

            # 转换为 markdown 格式
            if block.block_type == "title":
                md = f"# {block.content}\n"
            elif block.block_type.startswith("heading_"):
                level = int(block.block_type.split("_")[1])
                md = f"{'#' * (level + 1)} {block.content}\n"
            elif block.block_type == "list":
                md = f"{block.content}\n"
            elif block.block_type == "paragraph":
                md = f"{block.content}\n\n"
            elif block.block_type == "code":
                md = f"```\n{block.content}\n```\n\n"
            else:
                md = f"{block.content}\n\n"

            lines.append(md)
            tokens_used += block_tokens
            included += 1

        result = "".join(lines)
        if tokens_used >= max_tokens:
            result += f"\n\n[Truncated: {len(extracted.blocks) - included} lower-priority blocks omitted]\n"

        return result.strip()

    def extract_url_and_filter(
        self,
        url: str,
        attention_filter: AttentionFilter,
        min_priority: int = 1,
        max_tokens: int = 16000,
    ) -> str:
        """
        完整流程：从URL → 提取 → 过滤 → 输出 markdown
        需要 opendatalab extract 依赖
        """
        # extract-design 提取
        from extract_design import extract_url_to_markdown
        md = extract_url_to_markdown(url)
        extracted = self.extract_from_markdown(md, url)
        return self.filter_to_markdown(extracted, attention_filter, min_priority, max_tokens)


# ── 便捷接口 ────────────────────────────────────────────────────────

def extract_web_to_judgment_input(
    url: str,
    min_priority: int = 1,
    max_tokens: int = 16000,
) -> str:
    """
    便捷接口：URL → 过滤 → 直接输出给 judgment 十维分析的输入
    """
    from perception.attention_filter import AttentionFilter

    adapter = WebExtractorAdapter()
    af = AttentionFilter()
    return adapter.extract_url_and_filter(url, af, min_priority, max_tokens)
