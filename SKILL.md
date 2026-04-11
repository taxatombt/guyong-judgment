# guyong-juhuo — CoPaw Skill

## 基本信息

**name:** guyong-juhuo
**description:** guyong-juhuo Agent 系统。模拟具体个体、超越人类的 Agent。判断系统（judgment）是子系统之一，负责"遇到两难怎么想"。
**trigger:**

分类触发：
- 决策类：/(怎么选\|选哪个\|要不要\|值不值)/
- 冲突类：/(矛盾\|冲突\|纠结\|两难)/
- 分析类：/(复盘\|反思\|分析一下)/
- 通用：/利弊\|对方怎么处理\|博弈\|决策\|取舍/

## 最终目的

> agent 用了既可以**模仿固定的人**，也可以**超越人类**

## 铁律一

> 模拟人类意识，思想超越人类。

## 核心接口

```python
from judgment import check10d

result = check10d(
    task_text,           # 任务描述
    agent_profile=None,  # 可选：{"name": "<persona>", "values": [...], "biases": [...]}
    complexity="auto"    # auto | simple | complex | critical
)
```

返回 dict（机器可解析）：

```json
{
  "task": "工作很矛盾，不知道先做哪个",
  "complexity": "complex",
  "must_check": ["cognitive", "game_theory", "economic", "dialectical", "emotional", "temporal"],
  "important": ["intuitive", "moral"],
  "skipped": ["metacognitive"],
  "questions": {
    "cognitive": ["我现在用的是直觉还是分析？", "..."],
    "game_theory": ["涉及哪些玩家？", "..."]
  },
  "answers": {},
  "agent_profile": {"name": "<persona>", "values": ["成就", "自由"]},
  "meta": {"total_dims": 10, "checked": 9, "skipped_count": 1}
}
```

## Pipeline v2（完整判断流水线）

```python
from judgment import check10d_full, PipelineConfig, format_full_report

# 完整 Pipeline：串起所有模块
result = check10d_full("要不要辞职创业", agent_profile_name="<persona>")
print(format_full_report(result))

# 定制 Pipeline
cfg = PipelineConfig(
    agent_profile_name="<persona>",
    enable_adversarial=True,
    enable_qiushi=True,
    enable_embedding=True,
    enable_lessons=True,
    confidence_threshold=0.5,
)
result = check10d_full("要不要移民", config=cfg)
```

返回包含：动态权重 + 十维检视 + 置信度 + 对抗性验证 + 求是检查 + Embedding相似决策 + 教训警告 + Profile盲区

## CLI 交互向导

```bash
python judgment_cli.py                      # 交互模式（逐维问答）
python judgment_cli.py "要不要辞职创业"    # single judgment
python judgment_cli.py --report "问题"     # 完整报告 + JSON
```

## Web 实时流

```bash
python judgment_web.py
# 访问 http://localhost:18765
```

SSE 流式输出，实时显示各维度分析过程。

## 单元测试

```bash
python test_dynamic_weights.py
python test_adversarial.py
```

## 配置文件

```python
from judgment.config import load_config, save_config

cfg = load_config()  # 自动找 ~/.judgment/config.yaml
cfg.set("weights.cognitive", 0.20)
save_config(cfg)
```

## 模仿模式

传入 agent_profile 时，框架自动注入个性化追问：

```
【<persona>会怎么想这个问题？】
【<persona>容易在过度分析上犯错，我有没有犯同样的错？】
【<persona>的价值排序是成就 > 自由，这个判断符合吗？】
```

## 超越模式

不传 agent_profile 时，十维作为纯通用框架，帮助 agent 在判断力上超越人类整体。

## 十维说明

### 四维基础（必须）

| 维度 | 来源 | 作用 |
|------|------|------|
| 认知心理学 | 卡尼曼 System 1/2 | 偏差检测、元认知 |
| 博弈论 | 纳什均衡/激励结构 | 玩家分析、策略推演 |
| 经济学 | 机会成本/边际分析 | 看清代价、不只看到收益 |
| 辩证唯物主义 | 实事求是/矛盾分析 | 事实先行、具体问题具体分析 |

### 六维进阶（重要）

| 维度 | 来源 | 作用 |
|------|------|------|
| 情绪智能 | Goleman 情绪智能 | 识别情绪信号、不被情绪绑架 |
| 直觉/第六感 | System 1 模式识别 | 快速判断、身体信号 |
| 价值/道德推理 | 伦理学 | 应不应该、超越功利计算 |
| 社会意识 | 群体心理学 | 识别从众压力、身份绑架 |
| 时间折扣 | 行为经济学 | 对抗人类短视、跨期决策 |
| 元认知 | 自我监控 | 思考我在怎么思考、认知校准 |

## 复杂度分级

| 级别 | 触发条件 | 必须检视 |
|------|---------|---------|
| simple | 怎么做/告诉我/是什么 | cognitive + economic |
| complex | 纠结/矛盾/要不要/两难 | 四基础 + 情绪 + 时间 |
| critical | 生死/法律/不可逆 | 全部十维 |

## 使用时机

**触发：** 复杂决策、矛盾冲突、纠结两难、涉及多方利益、需要权衡取舍。

**不触发：** 简单直接的问题、纯执行类任务。

## 设计目标

> agent 用了既可以**模仿固定的人**，也可以**超越人类**

框架让 AI 的判断力最终超越人类整体。
