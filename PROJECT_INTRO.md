# guyong-juhuo

> 在大模型基础上，模拟具体个体、超越人类的 Agent。

---

## 核心定位

**不是工具，是一个会成长的分身。**

判断系统（judgment）是 guyong-juhuo 的子系统之一。
判断解决"遇到两难怎么想"的问题，
但一个人之所以是这个人，还需要更多维度——

---

## 子系统矩阵

### 1. 判断系统（judgment） ✅ 完整

遇到两难怎么想。十维同时检视，结构化输出。

### 2. 因果记忆 — 跨时间成长

过去的选择如何影响现在？"三个月前我选A导致现在B"。

人类的记忆不是事件清单，是因果网。记忆不追踪因果链，就只是录音机。

### 3. 好奇心引擎 — 主动探索

不是等用户给任务。是"主动关心项目进展"、"主动发现信息缺口"。

内驱力不是任务，是想知道。

### 4. 目标系统 — 五年/十年尺度

判断解决"这一刻的两难"，但目标系统处理"大方向是什么，怎么拆解成可行动的里程碑"。

### 5. 自我模型 — 知道自己的盲区

跨时间积累"我擅长什么、不擅长什么、什么时候会犯什么类型的错"。

不只是单次判断的反思，是对自己的元认知。

### 6. 情感系统 — 情绪是信号不是噪音

焦虑提示风险，兴奋提示机会。追踪情绪变化模式，理解情绪背后的东西。

### 7. 自进化 — 闭环学习

每次错误都被自动分析、形成规则、下次不再犯。

不只是教训记录，是真正的闭环。

---

## 两个模式

- **模仿模式**：传入 agent_profile，框架强制对齐特定个体的判断方式
- **超越模式**：不传入 profile，框架覆盖人类所有思维维度，在判断力上超越人类整体

---

## 铁律

> **模拟谷翔宇（具体的人），超越人类整体（不是谷翔宇）。**

---

## 快速开始

```bash
git clone https://github.com/taxatombt/guyong-juhuo.git
cd guyong-juhuo
pip install -r requirements.txt

# 命令行判断一个两难问题
python cli.py "我应该接受这个offer还是继续找?"

# 获取今日好奇清单
python -c "from curiosity.curiosity_engine import CuriosityEngine; engine = CuriosityEngine(); print(engine.get_daily_list())"

# 查看目标树
python -c "from goal_system.goal_system import GoalSystem; system = GoalSystem(); print(system.format_hierarchy())"
```

## 仓库

https://github.com/taxatombt/guyong-juhuo
