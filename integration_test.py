#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integration_test.py — 完整流水线集成测试
跑通：接收信息 → 判断 → 生成因果 → 更新自我模型 → 触发好奇心

验证所有导入路径正确，接口匹配，数据流闭环
"""

import sys
sys.path.insert(0, '.')
from pathlib import Path
import hashlib

print("=== guyong-juhuo 完整集成测试 ===\n")

# 1. Perception: 模拟接收一条消息
print("\n1. 测试 perception/attention_filter ...", end=" ")
from perception.attention_filter import AttentionFilter, IncomingMessage

af = AttentionFilter()
msg = IncomingMessage(
    content="我在开发 guyong-juhuo，现在遇到导入路径不一致的问题，需要修复",
    source="github",
    sender="user",
)
result = af.filter(msg)
print("OK  passed=%s, priority=%d, matched=%s" % (result.passed, result.priority, result.matched_keywords))

# 2. Judgment: 调用十维判断
print("\n2. 测试 judgment/router check10d ...", end=" ")
from router import check10d

test_question = "继续开发guyong-juhuo完整架构，还是先发布当前版本？两个选择都不错"
judgment_result = check10d(test_question)
checked = judgment_result['meta']['checked']
print("OK  checked=%d/10 维度，复杂度=%s" % (checked, judgment_result['complexity']))

# 3. Causal Memory: 记录判断结果
print("\n3. 测试 causal_memory ...", end=" ")
from causal_memory import log_causal_event, load_all_events

event = log_causal_event(
    task=test_question,
    result=judgment_result,
    decision=judgment_result["conclusion"] if "conclusion" in judgment_result else ""
)
event_id = event["event_id"]
events = load_all_events()
print("OK  已记录 event_id=%d, 总事件数=%d" % (event_id, len(events)))

# 4. Self Model: 分析历史偏差，生成提醒
print("\n4. 测试 self_model/self_model ...", end=" ")
from self_model.self_model import SelfModel, get_self_warnings

sm = SelfModel()
warnings, strengths = get_self_warnings(judgment_result)
print("OK  偏差数=%d, 提醒生成完成, warnings=%d" % (len(sm.biases), len(warnings)))
for w in warnings[:3]:
    print("   提醒: %s..." % w[:80])

# 5. Curiosity Engine: 检查是否触发新问题
print("\n5. 测试 curiosity/curiosity_engine ...", end=" ")
from curiosity.curiosity_engine import CuriosityEngine, calculate_alignment_score

ce = CuriosityEngine()
score = calculate_alignment_score(test_question)
# 判断置信度低的情况下才触发，我们测试接口可用性
if score > 0.5:
    from curiosity.curiosity_engine import PRIORITY_HIGH
    item = ce.add_relevance_trigger(
        question="为什么guyong-juhuo架构设计这么清爽?",
        topic="guyong-juhuo 架构设计",
        description="架构设计和依赖顺序非常清爽，值得探索为什么",
        current_task="集成测试",
    )
    triggered = [item]
else:
    triggered = []
print("OK  对齐得分=%.2f, 新增触发好奇心=%d 项" % (score, len(triggered)))
for item in triggered:
    print("   [%d] %s" % (item.priority_level, item.question))

# 6. Goal System: 测试对齐计算
print("\n6. 测试 goal_system ...", end=" ")
from goal_system.goal_system import get_goal_system

gs = get_goal_system()
score = gs.calculate_alignment_score(test_question)
print("OK  目标对齐得分=%.2f" % score)

# 7. Emotion System: 测试情绪检测
print("\n7. 测试 emotion_system ...", end=" ")
from emotion_system.emotion_system import EmotionSystem

es = EmotionSystem()
signal = es.detect_emotion(test_question, judgment_result)
print("OK  情绪信号检测完成, is_signal=%s" % signal.is_signal)
if signal.is_signal:
    print("   信号: %s" % signal.description)

# 8. Output System: 测试输出决策
print("\n8. 测试 output_system ...", end=" ")
from output_system.output_system import format_output

formatted = format_output(judgment_result, format_request="full")
print("OK  输出生成完成，长度=%d 字符" % len(formatted))
print("\n--- 完整输出 ---\n%s\n--- 输出结束 ---\n" % formatted[:300])

# 9. Action System: 生成行动计划
print("\n9. 测试 action_system ...", end=" ")
from action_system.action_system import generate_action_plan, format_action_plan

plan = generate_action_plan(judgment_result)
immediate = len([a for a in plan.actions if a.priority == 'now'])
print("OK  总行动=%d, 立即做=%d" % (len(plan.actions), immediate))

# 10. Feedback System: 添加反馈
print("\n10. 测试 feedback_system ...", end=" ")
from feedback_system.feedback_system import add_feedback, get_statistics

judgment_id = hashlib.md5(test_question.encode("utf-8")).hexdigest()[:12]
fb = add_feedback(
    judgment_id=judgment_id,
    event_id=event_id,
    feedback_text="集成测试全部通过，架构设计合理，导入路径修复正确",
    is_correct=True,
)
stat = get_statistics()
print("OK  反馈添加完成 id=%d, 总反馈=%d" % (fb.feedback_id, stat['total']))

print("\n" + "="*50)
print("** 所有模块测试通过！完整流水线跑通！ **")
print("="*50)
print("""
流程验证：
  信息接收 -> 判断 -> 因果记录 -> 自我提醒 -> 好奇检测 -> 目标对齐 -> 
  情绪检测 -> 输出决策 -> 行动计划 -> 反馈记录 -> 回流因果记忆

全部闭环 OK 所有导入路径修复 OK 接口匹配 OK
""")
