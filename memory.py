"""
memory.py — 判断记忆系统

每次判断记入历史，用户反馈后更新学习记录。
支持查询相似历史、统计判断准确率、提取教训。
"""

import json, os
from pathlib import Path
from datetime import datetime
from .router import check10d_run
from . import causal_memory

MEMORY_DIR = Path(__file__).parent / "memory"
DECISIONS_FILE = MEMORY_DIR / "decisions.jsonl"
LESSONS_FILE = MEMORY_DIR / "lessons.json"


def init():
    """初始化 memory 目录"""
    MEMORY_DIR.mkdir(exist_ok=True)
    if not DECISIONS_FILE.exists():
        DECISIONS_FILE.write_text("", encoding="utf-8")
    if not LESSONS_FILE.exists():
        LESSONS_FILE.write_text("[]", encoding="utf-8")


def log_decision(task, result, decision, feedback=None):
    """
    记录一次判断

    参数:
        task: 任务描述
        result: check10d() 返回的结构
        decision: 最终决策（用户填写的结论）
        feedback: 反馈（"好" / "坏" / str）
    """
    init()
    entry = {
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
    }

    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 因果记忆快路径：记录事件并建立相似链接
    causal_memory.log_causal_event(task, result, decision, feedback)

    if feedback:
        _update_lessons(entry)
        _update_accuracy(entry)

    return entry


def _update_lessons(entry):
    """从反馈中提取教训"""
    lessons = get_lessons()

    # 简单规则：从 skipped dims 和 feedback 反推教训
    if entry.get("feedback") in ["坏", "bad", "wrong"]:
        skipped = entry.get("skipped", [])
        complexity = entry.get("complexity")
        task_type = _classify_task(entry["task"])

        for dim in skipped:
            lesson = {
                "timestamp": entry["timestamp"],
                "dimension": dim,
                "task_type": task_type,
                "complexity": complexity,
                "pattern": f"跳过{dim}维度导致判断失误",
                "count": 1,
            }

            # 合并相似教训
            merged = False
            for existing in lessons:
                if existing["dimension"] == dim and existing["task_type"] == task_type:
                    existing["count"] += 1
                    merged = True
                    break

            if not merged:
                lessons.append(lesson)

    lessons.sort(key=lambda x: x["count"], reverse=True)
    lessons = lessons[:50]  # 最多50条

    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)


def _update_accuracy(entry):
    """更新准确率统计"""
    # 简化版：只统计总数和好评数
    stats_file = MEMORY_DIR / "stats.json"
    stats = {"total": 0, "good": 0}
    if stats_file.exists():
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except:
            pass

    stats["total"] += 1
    if entry.get("feedback") in ["好", "good", "correct", "yes"]:
        stats["good"] += 1

    stats["accuracy"] = round(stats["good"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0

    stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def _classify_task(task):
    """简单分类任务类型"""
    task_lower = task.lower()
    if any(kw in task_lower for kw in ["辞职", "工作", "职业"]):
        return "career"
    if any(kw in task_lower for kw in ["合伙", "合作", "团队"]):
        return "collaboration"
    if any(kw in task_lower for kw in ["投资", "钱", "财务"]):
        return "finance"
    if any(kw in task_lower for kw in ["感情", "关系", "朋友"]):
        return "relationship"
    return "general"


def get_decisions(limit=20):
    """获取最近判断记录"""
    init()
    if not DECISIONS_FILE.exists():
        return []
    lines = DECISIONS_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = [json.loads(line) for line in reversed(lines[-limit:])]
    return entries


def get_lessons():
    """获取教训列表"""
    init()
    if not LESSONS_FILE.exists():
        return []
    return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))


def get_stats():
    """获取统计"""
    init()
    stats_file = MEMORY_DIR / "stats.json"
    if not stats_file.exists():
        return {"total": 0, "good": 0, "accuracy": 0}
    return json.loads(stats_file.read_text(encoding="utf-8"))


def recall_similar(task, limit=3):
    """查找相似的历史判断"""
    decisions = get_decisions(100)
    task_words = set(task.lower())

    scored = []
    for d in decisions:
        if not d.get("decision"):
            continue
        task_words_d = set(d["task"].lower())
        overlap = len(task_words & task_words_d)
        scored.append((overlap, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:limit]]


def suggest_skipped_dimensions(task, complexity):
    """
    根据历史教训，建议这次应该检视哪些维度
    """
    decisions = get_decisions(50)
    task_type = _classify_task(task)

    # 找出同类任务中，最常被跳过导致失误的维度
    lessons = get_lessons()
    relevant = [l for l in lessons if l["task_type"] == task_type and l["count"] >= 1]

    if not relevant:
        return []

    # 返回最常出问题的维度
    return [l["dimension"] for l in relevant[:3]]


def summary():
    """获取记忆摘要"""
    decisions = get_decisions()
    lessons = get_lessons()
    stats = get_stats()

    top_lessons = lessons[:5]
    recent = decisions[:5]

    return {
        "total_decisions": len(decisions),
        "stats": stats,
        "top_lessons": top_lessons,
        "recent_count": len(recent),
    }
