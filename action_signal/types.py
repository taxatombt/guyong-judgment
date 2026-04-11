#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
action_signal types — 行动信号类型定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


class ActionTypeEnum(str, Enum):
    """
    行动类型枚举 — 预定义常见行动类型
    机器人可以根据类型直接路由处理
    """
    # 语言输出
    SPEAK = "speak"           # 说话/输出文本
    THINK = "think"           # 内部思考（不输出给用户）
    RESPOND = "respond"       # 回复用户
    
    # 硬件/机器人行动
    MOVE = "move"             # 移动
    GRAB = "grab"             # 抓取
    RELEASE = "release"       # 释放
    ROTATE = "rotate"         # 旋转
    CLICK = "click"           # 点击（屏幕）
    
    # 软件操作
    OPEN_FILE = "open_file"   # 打开文件
    SAVE_FILE = "save_file"   # 保存文件
    RUN_COMMAND = "run_command" # 运行命令
    NAVIGATE = "navigate"     # 导航到URL/路径
    
    # 系统行动
    WAIT = "wait"             # 等待
    SLEEP = "sleep"           # 休眠
    SHUTDOWN = "shutdown"     # 关机
    
    # 自定义扩展
    CUSTOM = "custom"         # 自定义行动类型


@dataclass
class ActionSignal:
    """
    聚活标准化行动信号
    
    机器人/执行器接收到这个结构，可以直接解析执行
    所有字段类型明确，机器可读
    """
    # 基础标识
    action_id: str                    # 唯一行动ID
    session_id: str                  # 所属会话ID
    action_type: ActionTypeEnum      # 行动类型
    
    # 核心内容
    content: str                     # 行动内容
    # - SPEAK: 要说的文本
    # - MOVE: 目标坐标 "x,y"
    # - OPEN_FILE: 文件路径
    
    # 优先级调度
    priority: int = 5                # 优先级 1-5，5最高
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 时间约束
    deadline: Optional[str] = None   # 截止时间 ISO格式
    timeout_seconds: Optional[int] = None # 超时时间
    
    # 参数扩展 — 机器人特定参数放这里
    parameters: Dict = field(default_factory=dict)
    
    # 来源元数据 — 方便追溯
    metadata: Dict = field(default_factory=dict)
    """
    metadata 可包含：
    - judgment_id: 来自哪个十维判断
    - causal_link_id: 基于哪个因果记忆
    - goal_aligned: 是否符合长期目标
    - confidence: 置信度 0-1
    """
    
    # 状态
    executed: bool = False          # 是否已执行
    executed_at: Optional[str] = None
    success: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        """转换为字典，方便JSON序列化"""
        return {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "action_type": self.action_type.value,
            "content": self.content,
            "priority": self.priority,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "timeout_seconds": self.timeout_seconds,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "executed": self.executed,
            "executed_at": self.executed_at,
            "success": self.success,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ActionSignal":
        """从字典恢复"""
        data["action_type"] = ActionTypeEnum(data["action_type"])
        return cls(**data)


# 类型别名
ActionType = ActionTypeEnum
ActionSignalList = List[ActionSignal]
