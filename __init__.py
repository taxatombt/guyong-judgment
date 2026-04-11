"""
guyong-juhuo — 聚活：模拟具体个体、持续自我进化的 Agent

判断系统（judgment）是核心子系统之一，负责"遇到两难怎么想"。
整体定位：在大模型基础上，模拟特定个体，持续学习，最终超越人类整体。

7大进化功能：
1. 置信度量化 — 解决"不知道自己不知道"
2. 对抗性验证 — 魔鬼代言人视角
3. 维度权重动态化 — 避免一把尺量所有问题
4. 教训模式识别 — 从记录错误到预防错误
5. 与求是融合 — 实事求是的框架
6. Profile进化追踪 — 主动发现盲区
7. embedding语义匹配 — 从历史中学习

Usage:
    from judgment import check10d
    result = check10d("工作很矛盾，不知道先做哪个")

    from judgment.agent import JudgmentAgent
    agent = JudgmentAgent(profile_name="<persona>")
    agent.think("要不要辞职")

    # 新功能
    from judgment.confidence import assess_all_confidences
    from judgment.adversarial import quick_validate
    from judgment.dynamic_weights import get_dynamic_weights
    from judgment.qiushi_integration import quick_qiushi_check
    from judgment.lesson_recognition import get_pattern_warnings
    from judgment.profile_evolution import get_evolution_report
    from judgment.embedding_match import find_similar_decisions
"""

from .judgment_path import JudgmentPath
from .dimensions import DIMENSIONS
from .paths import PATHS
from .router import (
    check10d,
    check10d_run,
    route,
    format_report,
    format_structured,
)

# 新增模块
from .confidence import (
    ConfidenceScore,
    assess_dimension_confidence,
    assess_all_confidences,
    get_low_confidence_dims,
    format_confidence_report,
    # 分层置信度
    LayeredVerdict,
    CoreJudgment,
    ConditionalJudgment,
    BlindSpot,
    build_layered_verdict,
    format_layered_verdict,
    # 后悔预演
    CounterfactualScenario,
    HindsightResult,
    counterfactual_hindsight,
    format_hindsight,
)

from .adversarial import (
    Objection,
    AdversarialResult,
    generate_objections,
    validate_decision,
    format_adversarial_report,
    quick_validate,
)

from .dynamic_weights import (
    WeightConfig,
    get_dynamic_weights,
    get_task_complexity,
    detect_task_types,
    get_weighted_dimensions,
    format_weight_report,
    # Auto-evolver
    update_weights_from_outcome,
    get_evolved_weights,
    get_evolution_summary,
)

from .qiushi_integration import (
    QiushiVerdict,
    apply_qiushi_check,
    get_applicable_methods,
    format_qiushi_report,
    quick_qiushi_check,
)

from .lesson_recognition import (
    Lesson,
    PatternWarning,
    extract_lesson,
    get_pattern_warnings,
    get_lessons_report,
)

from .profile_evolution import (
    BlindSpot,
    EvolutionRecord,
    EvolutionReport,
    track_blind_spot,
    record_profile_update,
    get_blind_spots,
    get_evolution_report,
    suggest_profile_update,
)

from .embedding_match import (
    EmbeddingMatcher,
    find_similar_decisions,
    get_embedding,
    init_embedding_db,
)

# 目标层次建模
from .profile import (
    LIFE_ARCHETYPES,
    get_archetype_info,
    get_north_star_goals,
    get_current_pursuits,
    check_goals_alignment,
    format_goals_alignment_report,
)

# #5 预后追踪
from .outcome_tracker import (
    start_tracking,
    record_outcome,
    get_unresolved,
    get_accuracy_report,
    format_accuracy_report,
)

# #3 因果链
from .causal_chain import (
    build_causal_chain,
    format_causal_report,
)

# #1 递归触发
from .recursive_trigger import (
    should_trigger_recursive,
    get_trigger_questions,
    recursive_probe,
    format_probe_report,
)

# #2 元认知
from .metacognitive import (
    metacognitive_review,
    metacognitive_self_check,
    get_bias_checklist,
    format_meta_report,
)

# #4 多agent辩论
from .multi_agent_debate import (
    DEBATE_AGENTS,
    run_debate,
    format_debate_report,
)

# Pipeline 整合
from .pipeline import (
    PipelineConfig,
    check10d_full,
    format_full_report,
    format_guyong_json,
)


__all__ = [
    # 核心接口
    "check10d",
    "check10d_run",
    "route",
    "format_report",
    "format_structured",

    # 数据结构
    "JudgmentPath",
    "DIMENSIONS",
    "PATHS",

    # 置信度量化
    "ConfidenceScore",
    "assess_dimension_confidence",
    "assess_all_confidences",
    "get_low_confidence_dims",
    "format_confidence_report",

    # 对抗性验证
    "Objection",
    "AdversarialResult",
    "generate_objections",
    "validate_decision",
    "format_adversarial_report",
    "quick_validate",

    # 维度权重动态化
    "WeightConfig",
    "get_dynamic_weights",
    "get_task_complexity",
    "detect_task_types",
    "get_weighted_dimensions",
    "format_weight_report",

    # 与求是融合
    "QiushiVerdict",
    "apply_qiushi_check",
    "get_applicable_methods",
    "format_qiushi_report",
    "quick_qiushi_check",

    # 教训模式识别
    "Lesson",
    "PatternWarning",
    "extract_lesson",
    "get_pattern_warnings",
    "get_lessons_report",

    # Profile进化追踪
    "BlindSpot",
    "EvolutionRecord",
    "EvolutionReport",
    "track_blind_spot",
    "record_profile_update",
    "get_blind_spots",
    "get_evolution_report",
    "suggest_profile_update",

    # Embedding语义匹配
    "EmbeddingMatcher",
    "find_similar_decisions",
    "get_embedding",
    "init_embedding_db",

    # 目标层次建模
    "LIFE_ARCHETYPES",
    "get_archetype_info",
    "get_north_star_goals",
    "get_current_pursuits",
    "check_goals_alignment",
    "format_goals_alignment_report",

    # #5 预后追踪
    "start_tracking",
    "record_outcome",
    "get_unresolved",
    "get_accuracy_report",
    "format_accuracy_report",

    # #3 因果链
    "build_causal_chain",
    "format_causal_report",

    # #1 递归触发
    "should_trigger_recursive",
    "get_trigger_questions",
    "recursive_probe",
    "format_probe_report",

    # #2 元认知
    "metacognitive_review",
    "metacognitive_self_check",
    "get_bias_checklist",
    "format_meta_report",

    # #4 多agent辩论
    "DEBATE_AGENTS",
    "run_debate",
    "format_debate_report",

    # 因果记忆（底座新模块）
    "log_causal_event",
    "find_similar_events",
    "recall_causal_history",
    "inject_to_judgment_input",
    "infer_daily_causal_chains",
    "get_event_graph_stats",
    "load_all_events",
    "load_all_links",

    # 自我模型（底座生长层）
    "SelfModel",
    "KnownBias",
    "Strength",
    "init",
    "load_model",
    "save_model",
    "update_from_feedback",
    "build_from_causal_memory",
    "get_self_warnings",
    "format_self_report",

    # 好奇心引擎（生长层）
    "CuriosityItem",
    "TriggerInfo",
    "CuriosityEngine",
    "trigger_from_low_confidence",
    "trigger_from_causal_mismatch",
    "get_top_open",
    "resolve",
    "get_daily_list",
    "full_report",

    # 目标系统（生长层）
    "Goal",
    "GoalSystem",
    "add_goal",
    "set_completed",
    "get_current_alignment_score",
    "check_align",
    "format_hierarchy",
    "get_curiosity_priority_boost",

    # 情感系统（生长层）
    "EmotionDetection",
    "detect_emotion",
    "analyze_current_emotion",
    "format_emotion_report",
    "inject_emotion_signal",

    # 输出系统（生长层）
    "OutputSystem",
    "OutputDecision",
    "format_output",

    # 行动系统（执行层）
    "NextAction",
    "ActionPlan",
    "generate_action_plan",
    "format_action_plan",
    "mark_action_completed",
    "get_pending_actions",
    "get_daily_actions",

    # 反馈系统（进化层）
    "Feedback",
    "add_feedback",
    "load_all_feedback",
    "format_recent_feedback",
    "get_statistics",
    "format_statistics",

    # 感知层（输入层）
    "perception",
    "AttentionFilter",
    "AttentionItem",
    "IncomingMessage",
    "FilterResult",
    "PDFExtractorAdapter",
    "PDFBlock",
    "ExtractedPDF",
    "extract_pdf_to_judgment_input",
    "WebExtractorAdapter",
    "WebBlock",
    "ExtractedWeb",
    "extract_web_to_judgment_input",
]
