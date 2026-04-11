#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_adapter.py — PDF 结构化提取适配器，对接 perception 注意力过滤

功能:
  1. 从 PDF 文件提取结构化文本（标题+段落，基于 opendatalab-pdf）
  2. 每个块分配优先级 → 标题 > 正文，关键词匹配提优先级
  3. 输出给 AttentionFilter → 过滤后进入判断 pipeline

对接 guyong-juhuo 架构:
  PDF → extract → structured blocks → priority assign → AttentionFilter → Judgment
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from perception.attention_filter import (
    AttentionFilter,
    IncomingMessage,
    FilterResult,
)


@dataclass
class PDFBlock:
    """PDF 提取出的结构化块"""
    block_type: str  # title / heading / paragraph / list / table
    level: int        # 标题层级 1-6
    content: str     # 文本内容
    page_num: int    # 页码
    priority: int = 0  # 计算出的优先级 0-5


@dataclass
class ExtractedPDF:
    """提取完成的完整 PDF 结构"""
    title: str
    blocks: List[PDFBlock]
    total_pages: int
    metadata: Dict = field(default_factory=dict)


class PDFExtractorAdapter:
    """
    PDF 提取适配器 → 对接 opendatalab-pdf 输出 → 输出优先级排序块
    
    使用:
        adapter = PDFExtractorAdapter()
        extracted = adapter.extract("document.pdf")
        filtered = adapter.filter_to_markdown(extracted, attention_filter)
    """

    def __init__(self):
        # 优先级基准
        self.base_priority = {
            "title":    5,  # 文档主标题
            "heading_1": 4, # H1
            "heading_2": 3, # H2
            "heading_3": 2, # H3
            "paragraph": 2, # 正文
            "list":       2, # 列表
            "table":      1, # 表格
        }

    def extract_from_markdown(self, markdown_text: str, metadata: Optional[Dict] = None) -> ExtractedPDF:
        """
        从已经提取好的 markdown 解析结构化块
        （opendatalab-pdf 输出 markdown，这里解析标题层级）
        """
        blocks = []
        lines = markdown_text.splitlines()
        current_page = 1
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
                blocks.append(PDFBlock(
                    block_type=block_type,
                    level=level,
                    content=content,
                    page_num=current_page,
                ))
            # 检测列表
            elif line.startswith(('- ', '* ', '+ ', '1. ', '2. ')):
                blocks.append(PDFBlock(
                    block_type="list",
                    level=0,
                    content=line,
                    page_num=current_page,
                ))
            # 普通段落
            else:
                # 合并同段落（如果前一个也是段落）
                if blocks and blocks[-1].block_type == "paragraph":
                    blocks[-1].content += "\n" + line
                else:
                    blocks.append(PDFBlock(
                        block_type="paragraph",
                        level=0,
                        content=line,
                        page_num=current_page,
                    ))

            # 检测页码（简单启发式）
            if "Page " in line or "页码" in line:
                try:
                    for word in line.split():
                        if word.isdigit() and len(word) <= 3:
                            current_page = int(word)
                            break
                except:
                    pass

        if not title and blocks:
            # 拿第一个标题当标题
            first_heading = next((b for b in blocks if b.block_type.startswith("heading")), None)
            if first_heading:
                title = first_heading.content

        return ExtractedPDF(
            title=title,
            blocks=blocks,
            total_pages=current_page,
            metadata=metadata or {},
        )

    def assign_priority(
        self,
        extracted: ExtractedPDF,
        attention_filter: AttentionFilter,
    ) -> ExtractedPDF:
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
                source="pdf",
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
        extracted: ExtractedPDF,
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
        lines.append(f"# PDF: {extracted.title}\n")

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
            elif block.block_type == "table":
                md = f"\n| Table content: {block.content} |\n\n"
            else:
                md = f"{block.content}\n\n"

            lines.append(md)
            tokens_used += block_tokens
            included += 1

        result = "".join(lines)
        if tokens_used >= max_tokens:
            result += f"\n\n[Truncated: {len(extracted.blocks) - included} lower-priority blocks omitted]\n"

        return result.strip()

    def extract_and_filter(
        self,
        pdf_path: str,
        attention_filter: AttentionFilter,
        min_priority: int = 1,
        max_tokens: int = 16000,
    ) -> str:
        """
        完整流程：从文件 → 提取 → 过滤 → 输出 markdown
        需要已经有 opendatalab-pdf extract 输出 markdown
        """
        # 这里假设已经用 opendatalab-pdf 提取好了
        # 如果直接调用，我们调用 workspace_modules 的 extract
        from workspace_modules.opendatalab_pdf import extract_markdown
        md = extract_markdown(pdf_path)
        extracted = self.extract_from_markdown(md)
        return self.filter_to_markdown(extracted, attention_filter, min_priority, max_tokens)


# ── 便捷接口 ────────────────────────────────────────────────────────

def extract_pdf_to_judgment_input(
    pdf_path: str,
    min_priority: int = 1,
    max_tokens: int = 16000,
) -> str:
    """
    便捷接口：PDF → 过滤 → 直接输出给 judgment 十维分析的输入
    """
    from perception.attention_filter import AttentionFilter

    adapter = PDFExtractorAdapter()
    af = AttentionFilter()
    return adapter.extract_and_filter(pdf_path, af, min_priority, max_tokens)
