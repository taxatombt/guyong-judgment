# -*- coding: utf-8 -*-
"""
judgment_cli.py �?CLI 交互式判断向导（入口脚本�?

Usage:
    python judgment_cli.py                  # 交互模式
    python judgment_cli.py "要不要辞职创�?  # single judgment
    python judgment_cli.py --report         # 输出完整报告
"""
import sys, os, json
from pathlib import Path

# 确保 judgment 包可导入
_workspace = Path(__file__).parent
if str(_workspace) not in sys.path:
    sys.path.insert(0, str(_workspace))

from judgment.pipeline import check10d_full, format_full_report, PipelineConfig


def interactive_wizard():
    """交互式问答向�?""
    print("=" * 50)
    print("  guyong-juhuo 交互式判断向�?)
    print("=" * 50)
    print()

    task = input("【问题】请描述你的判断情境：\n> ").strip()
    if not task:
        print("问题不能为空�?)
        return

    print()
    profile_name = input("【Profile】使用哪个判断风格？（直接回车使用默认）：\n> ").strip() or None
    print()

    complexity_map = {"s": "simple", "n": "normal", "c": "complex", "x": "critical"}
    cplx_input = input("【复杂度】简�?s)/普�?n)/复杂(c)/重大(x)？（直接回车自动检测）：\n> ").strip()
    complexity = complexity_map.get(cplx_input.lower(), None)
    print()

    skip_input = input("【模块】要跳过的模块？（直接回车全部启用，如：qiushi lessons）：\n> ").strip()
    skip_modules = skip_input.split() if skip_input else []

    print("\n正在分析，请稍�?..\n")

    cfg = PipelineConfig(
        agent_profile_name=profile_name,
        complexity=complexity,
        enable_adversarial="adversarial" not in skip_modules,
        enable_qiushi="qiushi" not in skip_modules,
        enable_embedding="embedding" not in skip_modules,
        enable_lessons="lessons" not in skip_modules,
    )

    result = check10d_full(task, config=cfg)
    print(format_full_report(result))

    save = input("\n【保存】要保存这次判断到历史记录吗�?y/n)：\n> ").strip().lower()
    if save == "y":
        import sqlite3, hashlib
        db_path = Path(__file__).parent / "judgment" / "memory_db" / "decisions.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT, task_hash TEXT, embedding_cache TEXT,
                decision TEXT, rating INTEGER,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        task_hash = hashlib.md5(task.encode()).hexdigest()
        decision_summary = json.dumps({
            "verdict": (result.get("adversarial") or {}).get("verdict"),
            "qiushi_ok": (result.get("qiushi") or {}).get("is_qiushi", True),
            "top_dims": result.get("weighted_dims", [])[:3],
        }, ensure_ascii=False)
        c.execute("""
            INSERT OR REPLACE INTO decisions (task, task_hash, embedding_cache, decision, rating)
            VALUES (?, ?, NULL, ?, NULL)
        """, (task, task_hash, decision_summary))
        conn.commit()
        conn.close()
        print("已保存！")


def main():
    args = sys.argv[1:]

    if not args:
        interactive_wizard()
        return

    if args[0] == "--report":
        task = " ".join(args[1:]) if len(args) > 1 else input("请输入判断问题：\n> ").strip()
        result = check10d_full(task)
        print(format_full_report(result))
        print("\n--- JSON ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args[0] == "--help":
        print("""guyong-juhuo CLI

用法:
    python judgment_cli.py                      # 交互模式
    python judgment_cli.py <问题>                # single judgment
    python judgment_cli.py --report <问题>       # 完整报告 + JSON
    python judgment_cli.py --help                # 本帮�?
""")
        return

    task = " ".join(args)
    result = check10d_full(task)
    print(format_full_report(result))


if __name__ == "__main__":
    main()
