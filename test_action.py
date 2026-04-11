#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '.')

from router import check10d
from action_system.action_system import generate_action_plan, format_action_plan, get_daily_actions

# 端到端测试：判断 → 生成行动计划
result = check10d("我很焦虑，不知道选A还是B，现在两个机会都不错")
plan = generate_action_plan(result)

print(format_action_plan(plan))
print("\n" + "="*50 + "\n")
print(get_daily_actions())
