# guyong-juhuo

> 在大模型基础上，模拟具体个体、超越人类的 Agent。

**判断系统**（judgment）是 guyong-juhuo 的核心子系统之一，负责"遇到两难时怎么想"。

---

## 定位

guyong-juhuo 不是单一工具，是一个完整的 Agent 系统，目标是：

> 模拟谷翔宇（顾庸）—— 通过持续学习，在意识、思想、判断上超越人类。

**子系统矩阵：**

| 系统 | 核心问题 | 现状 |
|------|---------|------|
| 判断系统 | 遇到两难怎么想 | ✅ 完整 |
| 因果记忆 | 过去如何影响现在 | 🔶 进行中 |
| 好奇心引擎 | 主动探索什么 | 🔶 进行中 |
| 目标系统 | 五年方向是什么 | 🔶 进行中 |
| 自我模型 | 我自己的盲区在哪 | 🔶 进行中 |
| 情感系统 | 情绪在说什么 | 🔶 进行中 |
| 自进化 | 错误怎么变成规则 | 🔶 进行中 |

---

## 快速开始

```bash
git clone https://github.com/taxatombt/guyong-juhuo.git
cd guyong-juhuo
python cli.py                      # 交互模式
python cli.py "要不要辞职"          # 单次判断
python cli.py --profile "guyong" "工作矛盾怎么办"  # 模仿顾庸
```

---

## 核心接口

### 直接调用判断系统

```python
from judgment import check10d

result = check10d("要不要从大厂跳槽到创业公司")
print(result["complexity"])   # simple / complex / critical
print(result["dims"])          # 十维分析结果
```

### Agent 模式

```python
from judgment.agent import JudgmentAgent

agent = JudgmentAgent(profile_name="guyong")
agent.run(interactive=True)   # 交互式对话
agent.run(task="工作很矛盾，不知道先做哪个")
```

---

## 判断系统：十维

| 维度 | 核心问题 |
|------|---------|
| 认知心理学 | 直觉还是分析？偏差在哪？ |
| 博弈论 | 谁在场？各方激励是什么？ |
| 经济学 | 放弃什么？真实代价多少？ |
| 辩证唯物主义 | 符合实际吗？主要矛盾？ |
| 情绪智能 | 情绪是信号还是噪音？ |
| 直觉/第六感 | 第一反应可信吗？ |
| 道德推理 | 应不应该，不是值不值 |
| 社会意识 | 我在做自己还是在演别人？ |
| 时间折扣 | 5年后还正确吗？ |
| 元认知 | 我在想什么？盲区在哪？ |

---

## 项目结构

```
guyong-juhuo/
├── judgment/              # 判断系统（子系统）
│   ├── dimensions.py       # 十维定义
│   ├── router.py          # 核心接口
│   └── judgment_path.py
├── memory/                # 因果记忆（子系统）
├── curiosity/             # 好奇心引擎（子系统）
├── goals/                 # 目标系统（子系统）
├── selfmodel/             # 自我模型（子系统）
├── emotion/               # 情感系统（子系统）
├── evolver/               # 自进化系统（子系统）
├── profiles/              # 个体模拟配置
├── cli.py                 # 统一入口
└── agent.py               # Agent 主程序
```

---

## License

MIT
