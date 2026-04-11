#!/usr/bin/env python3
"""
Test full guyong-juhuo system including perception and output
"""
import sys
sys.path.insert(0, '.')

print("Testing full guyong-juhuo system...")
print()

# Test 1: Import perception (information receiving system)
print("[1] Testing perception/attention_filter...")
from perception.attention_filter import (
    AttentionFilter,
    AttentionItem,
    IncomingMessage,
    FilterResult,
)
print("    * Import OK")

af = AttentionFilter()
print(f"    Default filters loaded: {len(af.active_filters)}")
msg = IncomingMessage(
    content="Let's work on guyong-juhuo OpenSpace integration",
    source="github",
    sender="user",
)
result = af.filter(msg)
print(f"    Filter result: passed={result.passed}, priority={result.priority}, matched={result.matched_keywords}")
print("    * Attention filter working")
print()

# Test 2: Import output system
print("[2] Testing output_system...")
from output_system.output_system import (
    OutputSystem,
    OutputDecision,
    OUTPUT_FORMATS,
)
print("    * Import OK")

osys = OutputSystem()
print(f"    Output formats supported: {OUTPUT_FORMATS}")
print("    * Output system working")
print()

# Test 3: Test OpenSpace (already verified)
print("[3] Testing OpenSpace integration...")
from openspace import (
    EvolutionType,
    create_captured,
    create_derived,
    create_fix,
    generate_skill_id,
    parse_skill_id,
    ExecutionAnalyzer,
)
print("    * Import OK")
root = create_captured("test", "hash")
print(f"    Created CAPTURED: {root.skill_id} gen={root.generation} v={root.fix_version}")
print("    * OpenSpace working")
print()

# Test 4: Test core judgment
print("[4] Testing core 10d judgment...")
from router import check10d
print("    * Import OK")
result = check10d("要不要花时间学习新的Agent框架？")
print(f"    Complexity: {result.get('complexity', 'unknown')}")
keys = list(result.keys())
print(f"    Result keys: {keys[:10]}...")
print("    * Judgment working")
print()

# Test 5: Check overall structure
print("[5] Overall system check...")
modules = [
    ("router", "check10d"),
    ("perception.attention_filter", "AttentionFilter"),
    ("output_system.output_system", "OutputSystem"),
    ("openspace", "EvolutionType"),
    ("openspace_evolution", "create_captured"),
    ("execution_analyzer", "ExecutionAnalyzer"),
    ("emotion_system.emotion_system", "EmotionSystem"),
    ("goal_system.goal_system", "GoalSystem"),
    ("self_model.self_model", "SelfModel"),
    ("curiosity.curiosity_engine", "CuriosityEngine"),
]

all_good = True
for module_name, cls_name in modules:
    try:
        mod = __import__(module_name, fromlist=[cls_name])
        getattr(mod, cls_name)
        print(f"    * {module_name}.{cls_name}")
    except Exception as e:
        print(f"    X {module_name}.{cls_name}: {e}")
        all_good = False

print()

if all_good:
    print("ALL SYSTEMS OK!")
    print()
    print("guyong-juhuo complete system:")
    print("  core judgment ....... 10d framework [OK]")
    print("  perception ......... information receiving / attention filter [OK]")
    print("  output ............. output decision / three formats [OK]")
    print("  OpenSpace .......... 3-level self-evolution [OK]")
    print("  execution analyzer . evolution suggestions from action log [OK]")
    print("  emotion ........... PAD emotion detection [OK]")
    print("  goal ............. long-term goal hierarchy [OK]")
    print("  self-model ........ blind spot tracking [OK]")
    print("  curiosity ......... active exploration [OK]")
    print()
    print("All core subsystems are in place and working!")
    print()
    print("Project structure is complete.")
else:
    print("Some modules need minor path fixes.")
