#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
causal_memory.py — 因果记忆模块

快路径：每次判断完成 → 立即写入因果事件节点
慢路径：每日一次 → 推断跨事件因果链
召回：新判断进入 → 召回相关因果历史 → 注入 judgment 输入
集成：反馈自动更新自我模型（依赖 self_model）

Reference:
- MAGMA Temporal Resonant Graph Memory + t兄弟方案
- OpenSpace (HKUDS) 启发：三级进化模式 / 质量监控 / 级联更新
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import difflib

from .types import (
    CausalEvent,
    CausalLink,
    CausalLinkQuality,
    CausalRelation,
    EvolutionType,
    EvolutionSuggestion,
    CausalStats,
)

# 集成自我模型更新
try:
    from self_model.self_model import update_from_feedback
except ImportError:
    update_from_feedback = None

# 文件路径
CAUSAL_EVENTS_FILE = Path(__file__).parent / "causal_events.jsonl"
CAUSAL_LINKS_FILE = Path(__file__).parent / "causal_links.jsonl"
EVENT_GRAPH_FILE = Path(__file__).parent / "event_graph.json"

# 相似度阈值
SIMILARITY_THRESHOLD = 0.65
# 最大时间差（三个月内视为相关）
MAX_DAYS_DELTA = 90


def init():
    """初始化文件"""
    if not CAUSAL_EVENTS_FILE.exists():
        CAUSAL_EVENTS_FILE.write_text("", encoding="utf-8")
    if not CAUSAL_LINKS_FILE.exists():
        CAUSAL_LINKS_FILE.write_text("", encoding="utf-8")
    if not EVENT_GRAPH_FILE.exists():
        EVENT_GRAPH_FILE.write_text("{}", encoding="utf-8")


def log_causal_event(task: str, result: Dict, decision: str, feedback: Optional[str] = None, outcome: Optional[bool] = None) -> Dict:
    """
    快路径：记录一次判断作为因果事件
    - outcome: True=决策成功/正确, False=决策失败/错误
    """
    init()
    
    event = {
        "event_id": _next_event_id(),
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "complexity": result.get("complexity"),
        "dimensions_checked": result.get("meta", {}).get("checked", 0),
        "must_check": result.get("must_check", []),
        "important": result.get("important", []),
        "skipped": result.get("skipped", []),
        "agent_profile": result.get("agent_profile", {}).get("name") if result.get("agent_profile") else None,
        "decision": decision,
        "feedback": feedback,
        "outcome": outcome,
    }

    with open(CAUSAL_EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 立即搜索相似历史事件，如果找到就建立潜在因果链接
    similar_events = find_similar_events(task, max_results=3)
    for prev_event in similar_events:
        if prev_event["event_id"] != event["event_id"]:
            add_causal_link(
                from_event_id=prev_event["event_id"],
                to_event_id=event["event_id"],
                relation="similar_task",
                confidence=_task_similarity(prev_event["task"], task),
                inferred=False,
            )

    # 如果有反馈或结果，更新相关因果链接质量 + 触发级联标记
    if outcome is not None:
        # 更新指向这个事件的所有链接质量
        update_link_quality_for_event(event["event_id"], outcome)

    # 如果有反馈，自动更新自我模型
    if feedback is not None and update_from_feedback is not None:
        update_from_feedback(event)

    # 如果有明确失败，触发进化建议
    suggestions = []
    if outcome is False:
        suggestions = suggest_evolution()

    return {**event, "evolution_suggestions": suggestions}


def _next_event_id() -> int:
    """生成下一个事件ID"""
    if not CAUSAL_EVENTS_FILE.exists():
        return 1
    count = sum(1 for _ in open(CAUSAL_EVENTS_FILE, encoding="utf-8"))
    return count + 1


def _task_similarity(task1: str, task2: str) -> float:
    """计算两个任务描述的相似度"""
    return difflib.SequenceMatcher(None, task1.lower(), task2.lower()).ratio()


def find_similar_events(task: str, max_results: int = 5) -> List[Dict]:
    """查找相似任务事件"""
    if not CAUSAL_EVENTS_FILE.exists():
        return []
    
    n = max_results
    events = []
    with open(CAUSAL_EVENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                sim = _task_similarity(event["task"], task)
                if sim >= SIMILARITY_THRESHOLD:
                    event["_similarity"] = sim
                    events.append(event)
            except:
                continue
    
    events.sort(key=lambda x: x["_similarity"], reverse=True)
    return events[:n]


def add_causal_link(
    from_event_id: int,
    to_event_id: int,
    relation: str,
    confidence: float,
    inferred: bool = False,
    evolution_type: Optional[str] = None,
    parent_link_id: Optional[int] = None,
) -> CausalLink:
    """
    添加一条因果链接
    继承 OpenSpace：支持三级进化模式（FIX/DERIVED/CAPTURED）
    """
    link = CausalLink(
        link_id=_next_link_id(),
        from_event_id=from_event_id,
        to_event_id=to_event_id,
        relation=relation,
        confidence=confidence,
        timestamp=datetime.now().isoformat(),
        inferred=inferred,
        evolution_type=evolution_type,
        parent_link_id=parent_link_id,
    )

    # 保存到JSONL
    with open(CAUSAL_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(link.to_dict(), ensure_ascii=False) + "\n")

    return link


def _next_link_id() -> int:
    """生成下一个链接ID"""
    if not CAUSAL_LINKS_FILE.exists():
        return 1
    count = sum(1 for _ in open(CAUSAL_LINKS_FILE, encoding="utf-8"))
    return count + 1


def load_all_events() -> List[Dict]:
    """加载所有事件"""
    if not CAUSAL_EVENTS_FILE.exists():
        return []
    
    events = []
    with open(CAUSAL_EVENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except:
                continue
    return events


def load_all_links() -> List[CausalLink]:
    """加载所有因果链接（返回类型化对象）"""
    if not CAUSAL_LINKS_FILE.exists():
        return []
    
    links = []
    with open(CAUSAL_LINKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                links.append(CausalLink.from_dict(data))
            except:
                continue
    return links


def update_link_quality_for_event(event_id: int, outcome: bool):
    """
    更新指向该事件的所有链接质量记录
    如果链接指向的事件结果已知，记录这次应用是否成功
    借鉴 OpenSpace 全栈质量监控
    """
    all_links = load_all_links()
    updated = False

    for link in all_links:
        if link.to_event_id == event_id:
            # 这次应用的结果就是事件的outcome
            link.quality.record_application(outcome)
            updated = True

    if updated:
        # 重写整个文件（简单实现，文件不大可接受）
        with open(CAUSAL_LINKS_FILE, "w", encoding="utf-8") as f:
            for link in all_links:
                f.write(json.dumps(link.to_dict(), ensure_ascii=False) + "\n")


def mark_cascade_revalidation(link_id: int):
    """
    标记依赖此链接的所有上游链接需要重新验证
    借鉴 OpenSpace 级联进化：基础链接改变 → 所有依赖它的都要重新验证
    """
    all_links = load_all_links()
    link = next((l for l in all_links if l.link_id == link_id), None)
    if not link:
        return

    # 遍历所有链接，找到依赖此链接的
    for other_link in all_links:
        if link.link_id in other_link.quality.dependent_link_ids:
            if not other_link.quality.needs_revalidation:
                other_link.quality.mark_needs_revalidation()

    # 也标记当前链接
    link.quality.mark_needs_revalidation()

    # 保存
    with open(CAUSAL_LINKS_FILE, "w", encoding="utf-8") as f:
        for link in all_links:
            f.write(json.dumps(link.to_dict(), ensure_ascii=False) + "\n")


def fix_causal_link(
    link_id: int,
    new_confidence: Optional[float] = None,
    new_relation: Optional[str] = None,
) -> CausalLink:
    """
    FIX 模式：就地修正现有因果链接
    对应 OpenSpace FIX 进化模式
    """
    all_links = load_all_links()
    link = next((l for l in all_links if l.link_id == link_id), None)
    if not link:
        raise ValueError(f"Link {link_id} not found")

    if new_confidence is not None:
        link.confidence = new_confidence
    if new_relation is not None:
        link.relation = new_relation

    link.evolution_type = EvolutionType.FIX.value
    link.quality.last_checked = datetime.now().isoformat()

    # FIX 后触发级联更新标记
    mark_cascade_revalidation(link_id)

    # 保存
    with open(CAUSAL_LINKS_FILE, "w", encoding="utf-8") as f:
        for lnk in all_links:
            f.write(json.dumps(lnk.to_dict(), ensure_ascii=False) + "\n")

    return link


def derive_causal_link(
    parent_link_id: int,
    from_event_id: int,
    to_event_id: int,
    relation: str,
    confidence: float,
) -> CausalLink:
    """
    DERIVED 模式：从父链接衍生特定场景版本
    对应 OpenSpace DERIVED 进化模式
    """
    all_links = load_all_links()
    parent = next((l for l in all_links if l.link_id == parent_link_id), None)
    if not parent:
        raise ValueError(f"Parent link {parent_link_id} not found")

    new_link = add_causal_link(
        from_event_id=from_event_id,
        to_event_id=to_event_id,
        relation=relation,
        confidence=confidence,
        inferred=False,
        evolution_type=EvolutionType.DERIVED.value,
        parent_link_id=parent_link_id,
    )

    # 新链接依赖父链接
    new_link.quality.dependent_link_ids.append(parent_link_id)

    # 保存更新
    all_links = load_all_links()  # reload
    with open(CAUSAL_LINKS_FILE, "w", encoding="utf-8") as f:
        for lnk in all_links:
            if lnk.link_id == new_link.link_id:
                f.write(json.dumps(new_link.to_dict(), ensure_ascii=False) + "\n")
            else:
                f.write(json.dumps(lnk.to_dict(), ensure_ascii=False) + "\n")

    return new_link


def capture_causal_link(
    from_event_id: int,
    to_event_id: int,
    relation: str,
    confidence: float,
) -> CausalLink:
    """
    CAPTURED 模式：捕获全新因果链接，无父级
    对应 OpenSpace CAPTURED 进化模式
    """
    return add_causal_link(
        from_event_id=from_event_id,
        to_event_id=to_event_id,
        relation=relation,
        confidence=confidence,
        inferred=False,
        evolution_type=EvolutionType.CAPTURED.value,
    )


def suggest_evolution() -> List[EvolutionSuggestion]:
    """
    扫描所有链接，建议需要进化的链接
    借鉴 OpenSpace 三种触发：低成功率/需要重新验证/依赖改变
    """
    all_links = load_all_links()
    suggestions = []

    for link in all_links:
        # 触发条件1：需要重新验证（级联标记）
        if link.quality.needs_revalidation:
            suggestions.append(EvolutionSuggestion(
                link_id=link.link_id,
                evolution_type=EvolutionType.FIX,
                reason="标记为需要重新验证（级联更新）",
                current_confidence=link.confidence,
                depends_on_changed=True,
            ))
            continue

        # 触发条件2：应用次数 >= 3，成功率 < 0.5
        if link.quality.applied_count >= 3 and link.quality.success_rate < 0.5:
            suggestions.append(EvolutionSuggestion(
                link_id=link.link_id,
                evolution_type=EvolutionType.FIX,
                reason=f"低成功率 ({link.quality.success_rate:.1%}), {link.quality.failed_count}/{link.quality.applied_count} 次失败",
                current_confidence=link.confidence,
            ))

    return suggestions


def get_links_needing_revalidation() -> List[CausalLink]:
    """获取所有需要重新验证的链接"""
    all_links = load_all_links()
    return [l for l in all_links if l.quality.needs_revalidation]


def recall_causal_history(task: str, max_events: int = 3) -> Dict:
    """
    召回因果历史给新判断：
    返回 {
        "similar_events": [...],  # 相似历史事件
        "causal_chains": [...],   # 指向这些事件的因果链接（含质量信息）
        "summary": str            # 自然语言总结给判断系统
    }
    """
    # Debug
    if not isinstance(max_events, int):
        print(f"DEBUG: recall_causal_history: max_events is {type(max_events)} = {max_events}")
        max_events = 3
    similar = find_similar_events(task, max_events)
    if not similar:
        return {
            "similar_events": [],
            "causal_chains": [],
            "summary": None,
        }
    
    links = load_all_links()
    relevant_links = []
    event_ids = [e["event_id"] for e in similar]
    
    for link in links:
        if link.from_event_id in event_ids or link.to_event_id in event_ids:
            relevant_links.append(link)
    
    # 生成自然语言总结
    summary_parts = []
    for i, event in enumerate(similar):
        outcome_str = ""
        if event.get("outcome") is True:
            outcome_str = "，上次决策正确"
        elif event.get("outcome") is False:
            outcome_str = "，上次决策错误"
        
        summary_parts.append(f"- 类似任务：{event['task'][:60]}{'...' if len(event['task'])>60 else ''}{outcome_str}")
        
        # 添加因果链接质量提示
        for link in relevant_links:
            if link.from_event_id == event["event_id"]:
                if link.quality.applied_count > 0:
                    summary_parts[-1] += f"（该模式成功率 {link.quality.success_rate:.1%}，{link.quality.applied_count} 次应用）"
                if link.quality.needs_revalidation:
                    summary_parts[-1] += " ⚠️ 需要重新验证"
    
    summary = "\n".join(summary_parts)
    
    return {
        "similar_events": similar,
        "causal_chains": [l.to_dict() for l in relevant_links],
        "summary": summary,
    }


def inject_to_judgment_input(task: str, current_input: str) -> str:
    """
    将因果历史注入判断输入
    在判断开始前自动召回相关历史，注入上下文
    """
    recall = recall_causal_history(task)
    if not recall["summary"]:
        return current_input
    
    injected = f"""\
# 因果历史参考（来自过去类似任务）

{recall["summary"]}

---

当前任务：
{current_input}
"""
    return injected


def get_statistics() -> CausalStats:
    """获取因果记忆统计信息"""
    events = load_all_events()
    links = load_all_links()
    
    by_evolution = {}
    total_success = 0
    total_applied = 0
    need_reval = 0
    
    for link in links:
        et = link.evolution_type or "original"
        by_evolution[et] = by_evolution.get(et, 0) + 1
        total_success += link.quality.success_count
        total_applied += link.quality.applied_count
        if link.quality.needs_revalidation:
            need_reval += 1
    
    avg_success = total_success / total_applied if total_applied > 0 else 0.0
    
    return CausalStats(
        total_events=len(events),
        total_links=len(links),
        inferred_links=sum(1 for l in links if l.inferred),
        fast_path_links=sum(1 for l in links if not l.inferred),
        by_evolution_type=by_evolution,
        avg_success_rate=avg_success,
        links_needing_revalidation=need_reval,
    )


def scan_low_quality_links() -> List[CausalLink]:
    """
    扫描低质量链接，触发进化
    对应 OpenSpace 指标监控触发器
    """
    return [
        link for link in load_all_links()
        if (
            (link.quality.applied_count >= 5 and link.quality.success_rate < 0.5)
            or link.quality.needs_revalidation
        )
    ]

    return [l for l in all_links if l.quality.needs_revalidation]


def infer_daily_causal_chains() -> int:
    """
    慢路径：每日扫描推断跨事件因果链
    返回：新添加的链接数
    """
    init()
    events = load_all_events()
    new_links = 0

    # 按时间排序
    events.sort(key=lambda x: x["timestamp"])

    # 遍历所有事件对，找潜在因果关系
    for i, e1 in enumerate(events):
        e1_time = datetime.fromisoformat(e1["timestamp"])
        for e2 in events[i+1:]:
            e2_time = datetime.fromisoformat(e2["timestamp"])
            delta = e2_time - e1_time
            if delta.days > MAX_DAYS_DELTA:
                continue
            
            # 同一任务类型，相似度高 → 很可能有因果影响
            sim = _task_similarity(e1["task"], e2["task"])
            if sim >= SIMILARITY_THRESHOLD:
                # 检查链接是否已存在
                all_links = load_all_links()
                exists = any(
                    (l.from_event_id == e1["event_id"] and 
                     l.to_event_id == e2["event_id"]) 
                    for l in all_links
                )
                if not exists:
                    capture_causal_link(
                        from_event_id=e1["event_id"],
                        to_event_id=e2["event_id"],
                        relation="influences",
                        confidence=sim * 0.8,  # 推断置信度打八折
                    )
                    new_links += 1

    return new_links


def recall_causal_history(task: str, max_events: int = 3) -> Dict:
    """
    召回因果历史给新判断：
    返回 {
        "similar_events": [...],  # 相似历史事件
        "causal_chains": [...],   # 指向这些事件的因果链接（含质量信息）
        "summary": str            # 自然语言总结给判断系统
    }
    """
    # Debug
    if not isinstance(max_events, int):
        print(f"DEBUG: recall_causal_history: max_events is {type(max_events)} = {max_events}")
        max_events = 3
    similar = find_similar_events(task, max_events)
    if not similar:
        return {
            "similar_events": [],
            "causal_chains": [],
            "summary": None,
        }
    
    links = load_all_links()
    relevant_links = []
    event_ids = [e["event_id"] for e in similar]
    
