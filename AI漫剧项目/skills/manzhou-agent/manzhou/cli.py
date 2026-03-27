"""
CLI 入口模块
manzhou agent 命令行工具
"""
import argparse
import os
from pathlib import Path
from .state_machine import DramStateMachine
from .chain_ref import ChainRef


def load_prompt_template(template_name: str) -> str:
    """加载 Prompt 模板"""
    prompts_dir = Path(__file__).parent / "prompts"
    template_path = prompts_dir / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在: {template_path}")
    return template_path.read_text(encoding="utf-8")


def extract_anchors(step_output: dict) -> dict:
    """从步骤输出中提取锚点"""
    return step_output.get("anchors", {})


def execute_prompt(prompt: str, user_input: str = None) -> str:
    """
    执行 Prompt（待接入 Claude API）
    目前返回提示信息，实际执行需要 Claude API
    """
    print(f"[CLI] 提示: 请在 Claude Code 中执行以下 Prompt:")
    print("=" * 60)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("=" * 60)
    if user_input:
        print(f"[CLI] 用户输入: {user_input[:200]}...")
    return "# 待Claude API执行"


def write_output(project_path: Path, filename: str, content: str):
    """写入输出文件"""
    output_path = project_path / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[CLI] ✓ 输出文件: {output_path}")


def init_project(args):
    """初始化新项目"""
    project_path = Path(args.project)
    if project_path.exists() and any(project_path.iterdir()):
        print(f"[CLI] 警告: 项目目录 {project_path} 已存在且非空")
        if not args.force:
            print("[CLI] 使用 --force 强制初始化")
            return

    project_path.mkdir(parents=True, exist_ok=True)
    print(f"[CLI] ✓ 项目初始化: {project_path}")


def run(args):
    """运行主流程"""
    project_path = Path(args.project)
    project_name = project_path.name

    if not project_path.exists():
        print(f"[CLI] 错误: 项目目录不存在: {project_path}")
        return

    sm = DramStateMachine(project_path=str(project_path), project_name=project_name)

    # 检查断点恢复
    recovery_point = sm.recovery.get_recovery_point()
    if recovery_point:
        print(f"[CLI] 🔄 从 {recovery_point} 恢复...")
        print(f"[CLI] 状态: {sm.status()}")

    # 根据当前状态执行下一步
    action = sm.get_next_action()

    if action == "ALL_DONE":
        print("[CLI] ✓ 项目已完成")
        return

    print(f"[CLI] → 执行动作: {action}")

    # 动作路由
    if action == "S0_PARSE_NOVEL":
        prompt = load_prompt_template("s0_parse_novel")
        output = execute_prompt(prompt, user_input=args.input)
        write_output(project_path, "S0-解析报告.md", output)
        sm.advance({"step": "S0", "anchors": {}})

    elif action == "S1_GLOBAL_SETTINGS":
        prompt = load_prompt_template("s1_global_settings")
        output = execute_prompt(prompt)
        write_output(project_path, "S1-风格指南.md", output)
        sm.advance({"step": "S1", "anchors": {"style": "v1.0.0"}})

    elif action == "S2_BUILD_CDP":
        prompt = load_prompt_template("s2_build_cdp")
        output = execute_prompt(prompt)
        write_output(project_path, "01-CDP资产包/CDP-JSON.md", output)
        sm.advance({"step": "S2", "anchors": {}})

    elif action == "S3_GENERATE_ASSETS":
        prompt = load_prompt_template("s3_generate_assets")
        output = execute_prompt(prompt)
        write_output(project_path, "02-资产库/生成任务表.md", output)
        sm.advance({"step": "S3", "anchors": {}})

    elif action == "S4_WRITE_SHOT_SCRIPTS":
        prompt = load_prompt_template("s4_write_shot_scripts")
        output = execute_prompt(prompt)
        write_output(project_path, "03-分镜脚本/分镜脚本总览.md", output)
        sm.advance({"step": "S4", "anchors": {}})

    elif action == "S5_GENERATE_VIDEO_PROMPTS":
        prompt = load_prompt_template("s5_video_prompts")
        output = execute_prompt(prompt)
        write_output(project_path, "04-视频生成/视频生成任务清单.md", output)
        sm.advance({"step": "S5", "anchors": {}})

    else:
        print(f"[CLI] 错误: 未知动作 {action}")
        return

    print(f"[CLI] ✓ 步骤完成，当前状态: {sm.state}")


def status(args):
    """查看项目状态"""
    project_path = Path(args.project)
    if not project_path.exists():
        print(f"[CLI] 错误: 项目目录不存在: {project_path}")
        return

    sm = DramStateMachine(project_path=str(project_path), project_name=project_path.name)
    status_info = sm.status()

    print(f"项目: {project_path.name}")
    print(f"当前状态: {status_info['state']}")
    print(f"下一步动作: {status_info['next_action']}")
    print(f"可继续: {'是' if status_info['can_proceed'] else '否'}")
    print(f"已完成步骤: {status_info['chain_ref_steps']}")


def reset(args):
    """重置项目状态"""
    project_path = Path(args.project)
    checkpoint_dir = project_path / ".manzhou"

    if checkpoint_dir.exists():
        import shutil
        shutil.rmtree(checkpoint_dir)
        print(f"[CLI] ✓ 已重置项目状态: {checkpoint_dir}")
    else:
        print(f"[CLI] 项目未初始化状态")


def main():
    parser = argparse.ArgumentParser(description="漫舟 Agent - AI 漫剧智能创作系统")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化新项目")
    init_parser.add_argument("project", help="项目路径")
    init_parser.add_argument("--force", action="store_true", help="强制初始化")

    # run 子命令
    run_parser = subparsers.add_parser("run", help="运行主流程")
    run_parser.add_argument("project", help="项目路径")
    run_parser.add_argument("--input", help="输入文件路径")

    # status 子命令
    status_parser = subparsers.add_parser("status", help="查看项目状态")
    status_parser.add_argument("project", help="项目路径")

    # reset 子命令
    reset_parser = subparsers.add_parser("reset", help="重置项目状态")
    reset_parser.add_argument("project", help="项目路径")

    args = parser.parse_args()

    if args.command == "init":
        init_project(args)
    elif args.command == "run":
        run(args)
    elif args.command == "status":
        status(args)
    elif args.command == "reset":
        reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
