#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试因果记忆模块"""

import sys
sys.path.insert(0, 'E:\\guyong-juhuo')

# 作为包导入
from guyong_juhuo import causal_memory
from guyong_juhuo import router

print("=== 测试因果记忆模块 ===")

# 测试初始化
stats = causal_memory.get_event_graph_stats()
print(f"初始化完成：{stats}")

# 测试判断入口注入
print("\n=== 测试判断入口 ===")
result = router.check10d("这个offer要不要接受")
print(f"返回结构正常：")
print(f"  - task: {result['task'][:50]}...")
print(f"  - original_task: {result['original_task']}")
print(f"  - has_causal_history: {result['causal_memory']['has_history']}")
print(f"  - 相似事件数量: {len(result['causal_memory']['similar_events'])}")

# 测试记录一个事件
print("\n=== 测试记录事件 ===")
from datetime import datetime
sample_result = {
    "complexity": "complex",
    "meta": {"checked": 8},
    "must_check": ["game_theory", "emotional"],
    "important": ["dialectical"],
    "skipped": ["metacognitive"],
    "agent_profile": {"name": "guyong"}
}
event = causal_memory.log_causal_event("这个offer要不要接受", sample_result, "accept", "good")
print(f"记录事件成功：event_id={event['event_id']}")

stats2 = causal_memory.get_event_graph_stats()
print(f"统计更新：{stats2}")

print("\n✅ 所有测试通过")
