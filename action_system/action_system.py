#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
action_system.py — 行动系统 最小可用版

核心问题：**决定了之后，怎么变成实际行动？需要做什么？下一步是什么？**

设计原则：
- 从小处开始，只做核心：把判断结果拆解成「下一步具体行动」
- 四个行动优先级分类：立即做 / 明天做 / 找人做 / 攒资源再做
- 行动结果记录 → 自动回流因果记忆 → 下次判断可用
- 松耦合：只依赖判断结果，不侵入前面模块

核心功能：
1. 从完整判断结果中拆解出下一步行动
2. 优先级分类，自动推荐顺序
3. 记录行动和结果
4. 完成后自动写回因果记忆闭环
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

# 文件路径
ACTION_LOG_FILE = Path(__file__).parent.parent / "action_log.jsonl"


# 行动优先级
PRIORITY = {
    "now": "立即做（今天）",
    "tomorrow": "明天做（本周）",
    "delegate": "找人做（我不需要自己做）",
    "wait": "攒资源再做（条件不成熟）",
}


@dataclass
class NextAction:
    """一条下一步行动"""
    action_id: int
    description: str
    priority: str  # now / tomorrow / delegate / wait
    related_question: str  # 来自判断里的哪个问题
    created_at: str
    completed: bool = False
    result: str = ""  # 完成后的结果

    def to_dict(self):
        return {
            "action_id": self.action_id,
            "description": self.description,
            "priority": self.priority,
            "priority_label": PRIORITY.get(self.priority, self.priority),
            "related_question": self.related_question,
            "created_at": self.created_at,
            "completed": self.completed,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class ActionPlan:
    """完整行动计划"""
    judgment_task: str          # 关联的判断任务
    judgment_id: str            # 关联判断ID（时间戳）
    actions: List[NextAction]    # 下一步行动列表
    created_at: str
    completed_count: int = 0
    total_count: int = 0

    def to_dict(self):
        return {
            "judgment_task": self.judgment_task,
            "judgment_id": self.judgment_id,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at,
            "completed_count": self.completed_count,
            "total_count": self.total_count,
        }


def _next_action_id() -> int:
    """生成下一个行动ID"""
    actions = load_all_actions()
    if not actions:
        return 1
    max_id = max(a["action_id"] for a in actions)
    return max_id + 1


def load_all_actions() -> List[Dict]:
    """加载所有行动记录"""
    if not ACTION_LOG_FILE.exists():
        return []
    
    actions = []
    with open(ACTION_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if "action_id" in item:
                    actions.append(item)
            except:
                continue
    return actions


def generate_action_plan(judgment_result: Dict) -> ActionPlan:
    """
    从判断结果生成行动计划：
    - 从每个必须检查维度的回答里提取行动
    - 如果没有回答，基于问题生成建议行动
    """
    task = judgment_result["original_task"]
    jid = datetime.now().strftime("%Y%m%d%H%M")
    actions = []
    aid = _next_action_id()
    
    # 遍历所有必须检查的维度
    must_check = judgment_result.get("must_check", [])
    questions = judgment_result.get("questions", {})
    answers = judgment_result.get("answers", {})
    
    for dim_id in must_check:
        dim_questions = questions.get(dim_id, [])
        for q in dim_questions:
            # 如果已经回答，从回答提取行动
            answer = answers.get(dim_id, {}).get(q, "")
            action_desc = _question_to_action(q, answer)
            if action_desc:
                actions.append(NextAction(
                    action_id=aid,
                    description=action_desc,
                    priority=_suggest_priority(q, answer),
                    related_question=q,
                    created_at=datetime.now().isoformat(),
                ))
                aid += 1
    
    # 如果没有提取到行动，默认生成一个「整理所有维度回答，做出最终选择」
    if not actions:
        actions.append(NextAction(
            action_id=aid,
            description="整理所有维度分析，做出最终判断和选择",
            priority="now",
            related_question="最终结论",
            created_at=datetime.now().isoformat(),
        ))
    
    plan = ActionPlan(
        judgment_task=task,
        judgment_id=jid,
        actions=actions,
        created_at=datetime.now().isoformat(),
        total_count=len(actions),
        completed_count=0,
    )
    
    # 保存计划
    save_action_plan(plan)
    return plan


def _question_to_action(question: str, answer: str) -> str:
    """把问题+回答转换成行动描述"""
    if not answer:
        # 没回答，问题就是行动
        return f"思考并回答：{question}"
    
    # 有回答，基于回答生成行动
    lower_q = question.lower()
    
    if "确认" in lower_q or "验证" in lower_q:
        return f"确认验证：{answer}"
    if "找" in lower_q or "分析" in lower_q:
        return f"分析完成：{answer} → 根据分析行动"
    if "怎么做" in lower_q or "如何" in lower_q:
        return f"执行：{answer}"
    
    # 默认：基于回答行动
    return f"{question} → 结论：{answer} → 按结论行动"


def _suggest_priority(question: str, answer: str) -> str:
    """根据问题和回答建议优先级"""
    lower_q = question.lower()
    lower_a = answer.lower()
    
    # 风险/现在就要解决 → 立即做
    if any(w in lower_q for w in ["风险", "焦虑", "立即", "现在", "今天"]):
        return "now"
    if any(w in lower_a for w in ["现在做", "立即", "今天"]):
        return "now"
    
    # 需要收集信息/准备 → 明天/本周做
    if any(w in lower_q for w in ["收集", "准备", "了解", "调研"]):
        return "tomorrow"
    
    # 别人负责 → 找人做
    if any(w in lower_q for w in ["对方", "他们", "别人", "负责人"]):
        return "delegate"
    
    # 需要资源/条件不成熟 → 等
    if any(w in lower_q for w in ["条件", "资源", "成熟", "未来"]):
        return "wait"
    
    # 默认现在做
    return "now"


def save_action_plan(plan: ActionPlan):
    """保存行动计划到日志"""
    with open(ACTION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(plan.to_dict(), ensure_ascii=False) + "\n")


def mark_action_completed(action_id: int, result: str):
    """标记行动完成，记录结果，并回流因果记忆"""
    from causal_memory.causal_memory import add_causal_event
    
    # 重新写入全部（简单实现，以后可以优化）
    all_plans = []
    updated = False
    with open(ACTION_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            plan = json.loads(line)
            found = False
            for action in plan["actions"]:
                if action["action_id"] == action_id:
                    action["completed"] = True
                    action["result"] = result
                    plan["completed_count"] += 1
                    found = True
                    updated = True
                    break
            all_plans.append(plan)
    
    # 写回
    with open(ACTION_LOG_FILE, "w", encoding="utf-8") as f:
        for p in all_plans:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    
    # 回流因果记忆：把行动结果作为反馈
    if updated:
        # 找计划
        for p in all_plans:
            for a in p["actions"]:
                if a["action_id"] == action_id:
                    add_causal_event(
                        task=p["judgment_task"],
                        decision=a["description"],
                        feedback=f"行动结果：{result}",
                    )
                    break
        return True
    
    return False


def format_action_plan(plan: ActionPlan) -> str:
    """生成人类可读行动计划"""
    lines = [
        f"=== 行动计划 ===\n",
        f"判断任务：{plan.judgment_task[:80]}",
        f"生成时间：{plan.created_at[:19]}",
        f"总行动：{plan.total_count}，已完成：{plan.completed_count}",
        "",
    ]
    
    # 按优先级分组输出
    grouped = {
        "now": [],
        "tomorrow": [],
        "delegate": [],
        "wait": [],
    }
    for action in plan.actions:
        grouped[action.priority].append(action)
    
    for p in ["now", "tomorrow", "delegate", "wait"]:
        if not grouped[p]:
            continue
        label = PRIORITY[p]
        lines.append(f"## {label}")
        for idx, action in enumerate(grouped[p], 1):
            mark = "✓" if action.completed else " "
            lines.append(f"  [{mark}] {idx}. {action.description}")
            if action.completed and action.result:
                lines.append(f"       → 结果：{action.result[:60]}")
        lines.append("")
    
    lines.append("---")
    lines.append("完成行动后标记：mark_action_completed(action_id, result) → 自动回流因果记忆")
    
    return "\n".join(lines)


def get_pending_actions(only_priority: Optional[str] = None) -> List[Dict]:
    """获取所有待完成行动，可选按优先级过滤"""
    all_actions = []
    all_plans_data = load_all_actions()
    for plan in all_plans_data:
        for action in plan["actions"]:
            if not action["completed"]:
                if only_priority is None or action["priority"] == only_priority:
                    action["judgment_task"] = plan["judgment_task"]
                    all_actions.append(action)
    
    # 按优先级排序：now > tomorrow > delegate > wait
    priority_order = ["now", "tomorrow", "delegate", "wait"]
    all_actions.sort(key=lambda x: priority_order.index(x["priority"]))
    
    return all_actions


def get_daily_actions() -> str:
    """获取今日待做行动（优先级now），人类可读"""
    pending = get_pending_actions("now")
    if not pending:
        return "今日没有待立即执行的行动。"
    
    lines = ["=== 今日待做行动 ===\n"]
    for idx, action in enumerate(pending, 1):
        lines.append(f"{idx}. [{action['priority_label']}] {action['description']}")
        lines.append(f"   来自：{action['judgment_task'][:40]}")
    return "\n".join(lines)


# 测试
if __name__ == "__main__":
    from router import check10d
    
    result = check10d("我很焦虑，不知道选A还是B，现在两个机会都不错")
    plan = generate_action_plan(result)
    print(format_action_plan(plan))
    print("\n=== 今日待做 ===")
    print(get_daily_actions())
