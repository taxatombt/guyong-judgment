"""
execution_analyzer.py —— 执行日志分析 → 生成进化建议

聚活适配：基于 OpenSpace 设计，但 fitness 目标是**个人一致性**不是通用任务成功率

- 每次判断执行后记录"这次判断是否符合个人一贯决策风格"
- 分析各知识单元一致性得分 → 生成进化建议
- 优先级：自我模型 > 因果记忆 > 判断规则 > 通用技能
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from openspace_evolution import (
    EvolutionType,
    KnowledgeCategory,
    SkillLineage,
    SkillMetrics,
    load_skill_db,
    suggest_evolution,
    save_skill_db,
    SKILL_DB_PATH,
    save_system_snapshot,
)


@dataclass
class ExecutionRecord:
    """聚活单次执行记录

    success 在这里定义为"是否符合个人决策一致性"，不是任务客观成功
    哪怕任务失败了，但只要这个决策确实是你会做的，也算"成功"（一致性意义上）
    """
    timestamp: str
    skill_id: str
    skill_name: str
    is_consistent: bool       # 聚活：是否符合个人一贯决策风格
    consistency_score: float = 1.0  # 0.0 ~ 1.0 一致性打分
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    knowledge_category: Optional[str] = None
    metadata: Optional[dict] = None

    @property
    def success(self) -> bool:
        """保持 OpenSpace 兼容"""
        return self.is_consistent


class ExecutionAnalyzer:
    """
    聚活：分析执行日志 → 更新知识单元指标 → 生成进化建议

    核心适配：fitness = 个人一致性得分，不是通用任务成功率
    - 目标：保留"这就是你会做的选择"，哪怕按通用标准它是错的
    - 进化触发：一致性偏低的知识单元会被建议修正
    - 优先级：自我模型 > 因果记忆 > 判断规则
    """

    def __init__(
        self,
        action_log_path: Path = None,
        skill_db_path: Path = SKILL_DB_PATH,
        consistency_threshold: float = 0.5,
        min_applications: int = 3,
        auto_snapshot: bool = True,
    ):
        self.action_log_path = action_log_path or Path(__file__).parent / "action_log.jsonl"
        self.skill_db_path = skill_db_path
        self.consistency_threshold = consistency_threshold
        self.min_applications = min_applications
        self.auto_snapshot = auto_snapshot  # 聚活：更新后自动全系统快照

    def load_execution_records(self) -> List[ExecutionRecord]:
        """Load all execution records from action_log.jsonl"""
        records = []
        if not self.action_log_path.exists():
            return records

        with open(self.action_log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # 兼容旧格式
                    is_consistent = data.get("is_consistent", data.get("success", False))
                    rec = ExecutionRecord(
                        timestamp=data.get("timestamp", ""),
                        skill_id=data.get("skill_id", ""),
                        skill_name=data.get("skill_name", ""),
                        is_consistent=is_consistent,
                        consistency_score=data.get("consistency_score", 1.0 if is_consistent else 0.0),
                        error=data.get("error"),
                        duration_ms=data.get("duration_ms"),
                        knowledge_category=data.get("knowledge_category"),
                        metadata=data.get("metadata"),
                    )
                    records.append(rec)
                except json.JSONDecodeError:
                    continue
        return records

    def aggregate_by_skill(self, records: List[ExecutionRecord]) -> Dict[str, Tuple[int, int, float]]:
        """Aggregate (total, consistent_count, avg_consistency) by skill_id"""
        agg = {}
        for rec in records:
            sid = rec.skill_id
            if sid not in agg:
                agg[sid] = (0, 0, 0.0)  # (total, consistent, avg_score)
            total, count_consistent, sum_score = agg[sid]
            total += 1
            if rec.is_consistent:
                count_consistent += 1
            sum_score += rec.consistency_score
            agg[sid] = (total, count_consistent, sum_score)
        return agg

    def update_skill_metrics(self) -> int:
        """
        Update skill metrics from execution records
        Returns number of updated skills
        """
        records = self.load_execution_records()
        if not records:
            return 0

        agg = self.aggregate_by_skill(records)
        db = load_skill_db(self.skill_db_path)
        updated = 0

        for sid, (total, count_consistent, sum_score) in agg.items():
            if sid in db:
                node = db[sid]
                # 更新指标：用日志中的聚合数据覆盖（简单可靠）
                avg_score = sum_score / total if total > 0 else 0.0
                node.metrics.applied_count = total
                node.metrics.success_count = count_consistent
                node.metrics.failed_count = total - count_consistent
                node.metrics.personal_consistency_score = avg_score
                updated += 1

        if updated > 0:
            save_skill_db(self.skill_db_path, db)
            # 聚活：更新后自动保存全系统快照
            if self.auto_snapshot:
                snapshot_path = save_system_snapshot(db)
                print(f"[聚活] 自动保存全系统快照: {snapshot_path}")

        return updated

    def get_low_consistency_skills(self) -> List[Tuple[SkillLineage, float]]:
        """Find skills with consistency below threshold"""
        db = load_skill_db(self.skill_db_path)
        result = []
        for node in db.values():
            if not node.is_active:
                continue
            # 聚活：锁定的知识不列入改进建议
            if node.metrics.is_locked:
                continue
            if node.metrics.applied_count >= self.min_applications:
                rate = node.metrics.consistency_rate
                if rate < self.consistency_threshold:
                    result.append((node, rate))
        return sorted(result, key=lambda x: x[1])

    def generate_evolution_suggestions(self) -> str:
        """Generate human-readable evolution suggestions"""
        self.update_skill_metrics()
        suggestions = suggest_evolution(load_skill_db(self.skill_db_path))

        lines = ["# 聚活执行分析 · 进化建议", ""]
        lines.append(f"一致性阈值: {self.consistency_threshold:.0%}, 最小应用次数: {self.min_applications}")
        lines.append("")

        if suggestions:
            lines.append(f"## 待进化知识单元 ({len(suggestions)} 个)")
            lines.append("")
            # 已经按优先级排序了（自我模型优先）
            for s in suggestions:
                cat = s.get("knowledge_category", "UNKNOWN")
                priority = s.get("priority", 0)
                lines.append(f"- **{s['skill_name']}** [{cat}, priority={priority}]")
                lines.append(f"  - 原因: {s['reason']}")
                lines.append(f"  - 当前一致性: {s['current_consistency']:.1%}")
                lines.append(f"  - 建议: {s['evolution_type']}")
                lines.append("")
        else:
            lines.append("✅ 所有知识单元一致性正常，没有待自动进化项目")
            lines.append("")

        # 统计信息
        db = load_skill_db(self.skill_db_path)
        stats = {
            "total": len(db),
            "active": sum(1 for n in db.values() if n.is_active),
            "locked": sum(1 for n in db.values() if n.metrics.is_locked),
        }
        lines.append(f"## 统计")
        lines.append(f"- 总知识单元: {stats['total']}")
        lines.append(f"- 活跃: {stats['active']}")
        lines.append(f"- 锁定（核心身份）: {stats['locked']}")
        lines.append("")

        return "\n".join(lines)

    def print_summary(self):
        """Print summary to console"""
        records = self.load_execution_records()
        agg = self.aggregate_by_skill(records)
        print(f"Loaded {len(records)} execution records")
        print(f"Aggregated to {len(agg)} skills")
        low = self.get_low_consistency_skills()
        print(f"Found {len(low)} skills below {self.consistency_threshold:.0%} threshold")
        for node, rate in low[:10]:
            cat = node.metrics.knowledge_category
            locked = "🔒 " if node.metrics.is_locked else ""
            print(f"  {locked}{node.skill_id} [{cat}]: {rate:.1%}")
        if len(low) > 10:
            print(f"  ... and {len(low) - 10} more")
