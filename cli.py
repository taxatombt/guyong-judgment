"""
cli.py — guyong-juhuo Agent 入口

用法:
    python cli.py                      # 交互模式
    python cli.py "任务描述"           # single judgment
    python cli.py --profile "<persona>" "任务"  # specify persona
    python cli.py pdf <file.pdf>       # 提取PDF并做十维分析
    python cli.py --list               # 列出所有 profile
    python cli.py --stats              # 查看统计
    python cli.py --lessons            # 查看教训
    python cli.py --history            # 查看历史
    python cli.py --evolution          # 生成OpenSpace进化建议
    python cli.py --create-profile "<persona>" --type rational  # 创建 profile
"""

import sys
import os
import json

pkg_dir = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(pkg_dir)
if parent not in sys.path:
    sys.path.insert(0, parent)


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print("guyong-juhuo Agent — 数字分身，持续自我进化")
        print()
        print("用法:")
        print("  python cli.py                      # 交互模式")
        print("  python cli.py \"任务描述\"           # 单次十维判断")
        print("  python cli.py --profile NAME \"任务\"  # 指定 persona")
        print("  python cli.py pdf <file.pdf>       # 提取PDF并做十维分析")
        print("  python cli.py web <url>            # 提取网页并做十维分析")
        print("  python cli.py --list                # 列出所有 profile")
        print("  python cli.py --stats               # 查看统计")
        print("  python cli.py --lessons             # 查看教训")
        print("  python cli.py --history             # 查看历史")
        print("  python cli.py --evolution          # 生成OpenSpace进化建议")
        print("  python cli.py --create-profile NAME --type rational  # 创建 profile")
        print()
        print("Profile 类型: rational / emotional / intuitive / balanced")
        sys.exit(0)

    profile_name = None
    task = None
    cmd_mode = None  # stats/lessons/history/list/evolution/pdf
    pdf_path = None
    create_profile = None
    create_type = "balanced"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--profile":
            profile_name = args[i + 1]
            i += 2
        elif arg == "--list":
            cmd_mode = "list"
            i += 1
        elif arg == "--stats":
            cmd_mode = "stats"
            i += 1
        elif arg == "--lessons":
            cmd_mode = "lessons"
            i += 1
        elif arg == "--history":
            cmd_mode = "history"
            i += 1
        elif arg == "--summary":
            cmd_mode = "summary"
            i += 1
        elif arg == "--evolution":
            cmd_mode = "evolution"
            i += 1
        elif arg == "pdf":
            cmd_mode = "pdf"
            pdf_path = args[i + 1]
            i += 2
        elif arg == "web":
            cmd_mode = "web"
            web_url = args[i + 1]
            i += 2
        elif arg == "--create-profile":
            create_profile = args[i + 1]
            i += 2
        elif arg == "--type":
            create_type = args[i + 1]
            i += 2
        elif not arg.startswith("--"):
            task = " ".join(args[i:])
            break
        else:
            i += 1

    # 命令模式
    if cmd_mode:
        from judgment.profile import list_profiles
        from judgment.memory import get_stats, get_lessons, get_decisions, summary as memory_summary

        if cmd_mode == "list":
            profiles = list_profiles()
            print("Profiles:", ", ".join(profiles) if profiles else "(空)")
            return
        elif cmd_mode == "stats":
            stats = get_stats()
            print(f"总判断数: {stats['total']}")
            print(f"正确判断: {stats['good']}")
            print(f"准确率: {stats['accuracy']:.1f}%")
            return
        elif cmd_mode == "lessons":
            lessons = get_lessons()
            if not lessons:
                print("暂无教训")
            for l in lessons[:10]:
                print(f"  [{l['count']}次] {l['dimension']}: {l['pattern']}")
            return
        elif cmd_mode == "history":
            decisions = get_decisions(10)
            for d in decisions:
                fb = d.get("feedback", "")
                print(f"  [{d['timestamp'][:10]}] {d['task'][:40]}: {d['decision'][:25]} [{fb}]")
            return
        elif cmd_mode == "summary":
            s = memory_summary()
            print(f"总判断数: {s['total_decisions']}")
            print(f"准确率: {s['stats']['accuracy']:.1f}%")
            print(f"教训数: {len(s['top_lessons'])}")
            return
        elif cmd_mode == "evolution":
            # OpenSpace 进化建议
            from execution_analyzer import ExecutionAnalyzer
            analyzer = ExecutionAnalyzer()
            suggestions = analyzer.generate_evolution_suggestions()
            print("=== OpenSpace 进化建议 ===")
            print()
            if not suggestions:
                print("没有需要进化的技能")
            else:
                for s in suggestions:
                    print(f"[{s['suggestion']}] skill={s['skill_id']} 成功率={s['success_rate']:.1%}")
                    print(f"  原因: {s['reason']}")
                    print()
            return
        elif cmd_mode == "pdf":
            # PDF提取 + 十维分析
            from perception import extract_pdf_to_judgment_input
            from judgment.router import check10d, format_report

            print(f"提取PDF: {pdf_path}")
            print("正在提取并过滤...")
            content = extract_pdf_to_judgment_input(pdf_path)
            print()
            print("=== 过滤后内容（前800字符）===")
            if len(content) > 800:
                print(content[:800] + "...\n(内容被截断，完整内容用于分析)")
            else:
                print(content)
            print()
            print("=== 十维分析结果 ===")
            result = check10d(content, profile_name=profile_name)
            print(format_report(result))
            return
        elif cmd_mode == "web":
            # 网页提取 + 十维分析
            from perception import extract_web_to_judgment_input
            from judgment.router import check10d, format_report

            print(f"提取网页: {web_url}")
            print("正在提取并过滤...")
            content = extract_web_to_judgment_input(web_url)
            print()
            print("=== 过滤后内容（前800字符）===")
            if len(content) > 800:
                print(content[:800] + "...\n(内容被截断，完整内容用于分析)")
            else:
                print(content)
            print()
            print("=== 十维分析结果 ===")
            result = check10d(content, profile_name=profile_name)
            print(format_report(result))
            return

    # 创建 profile
    if create_profile:
        from judgment.profile import create_persona
        p = create_persona(create_profile, create_type)
        print(f"已创建 profile: {p['name']} ({p['style']})")
        print(f"  价值观: {', '.join(p['values'])}")
        print(f"  已知偏差: {', '.join(p['biases'])}")
        return

    # 初始化 agent
    from judgment.agent import JudgmentAgent
    agent = JudgmentAgent(profile_name=profile_name)

    # 运行
    if task:
        agent.run(task=task)
    else:
        agent.run(interactive=True)


if __name__ == "__main__":
    main()
