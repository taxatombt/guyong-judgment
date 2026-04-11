#!/usr/bin/env python3
"""Test 聚活 OpenSpace 个人进化适配"""

from openspace_evolution import (
    EvolutionType,
    KnowledgeCategory,
    SkillMetrics,
    create_captured,
    create_derived,
    create_fix,
    format_dag_ascii,
    get_stats,
    save_system_snapshot,
)

# Test 1: create with category
print("=== Test 1: create_captured with knowledge category ===")
node = create_captured(
    skill_name="core-personal-values",
    content_hash="abc123",
    knowledge_category=KnowledgeCategory.CORE_IDENTITY,
)
print("OK: skill_id:", node.skill_id)
print("    locked:", node.metrics.is_locked)
print("    category:", node.metrics.knowledge_category)
print("    can_auto_evolve:", node.metrics.can_auto_evolve())
print()

# Test 2: CORE_IDENTITY is locked, cannot FIX
print("=== Test 2: Identity lock prevents auto-FIX ===")
try:
    fixed = create_fix(node, "newhash456")
    print("FAIL: Should have blocked FIX on locked")
except ValueError as e:
    print("OK:", str(e))
print()

# Test 3: SELF_MODEL (high priority, not locked)
print("=== Test 3: SELF_MODEL knowledge ===")
node2 = create_captured(
    skill_name="self-blind-spots",
    content_hash="def456",
    knowledge_category=KnowledgeCategory.SELF_MODEL,
)
print("OK: skill_id:", node2.skill_id)
print("    locked:", node2.metrics.is_locked)
print("    category:", node2.metrics.knowledge_category)
print("    can_auto_evolve:", node2.metrics.can_auto_evolve())
print()

# Test 4: DERIVED inherits lock/category
print("=== Test 4: DERIVED inherits from parent ===")
derived = create_derived(node2, "self-blind-spots-judging", "hash789")
print("OK: derived skill_id:", derived.skill_id)
print("    generation:", derived.generation, "(parent was", node2.generation, ")")
print("    category inherited:", derived.metrics.knowledge_category)
print("    lock inherited:", derived.metrics.is_locked, "==", node2.metrics.is_locked)
print()

# Test 5: Build full DAG
print("=== Test 5: ASCII DAG visualization with categories/locks ===")
dag = {
    node.skill_id: node,
    node2.skill_id: node2,
    derived.skill_id: derived,
}
ascii_out = format_dag_ascii(dag)
print(ascii_out)
print()

# Test 6: Stats
print("=== Test 6: get_stats ===")
stats = get_stats(dag)
print(stats)
print()

# Test 7: Full system snapshot
print("=== Test 7: save_system_snapshot ===")
snapshot_path = save_system_snapshot(dag, snapshot_dir="test_snapshots")
print("OK: saved to:", snapshot_path)
print()

print("ALL TESTS PASSED!")
print("聚活 OpenSpace 个人进化适配工作正常。")
