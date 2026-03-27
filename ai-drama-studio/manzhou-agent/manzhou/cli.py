#!/usr/bin/env python3
"""
漫舟导演Agent CLI v10.1.0（简化版）
用法: manzhou run <项目目录>
      manzhou generate <项目目录> [--episode 1]
      manzhou status <项目目录>

流程: Step 0 → Step 7（分镜脚本）截止
      manzhou generate → Qwen3-Max 自动生成 Prompt
"""

import argparse
import json
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from manzhou.constants import (
    StepID, StepStatus, STEP_ORDER, QUALITY_DIMENSIONS,
    DIALOGUE_MAX_CHARS, SHOT_DURATION_DEFAULT,
    EPISODE_DURATION_DEFAULT, STYLE_PRESETS, PLATFORM_SPECS,
)
from manzhou.schema import (
    ProjectConfig, EpisodeShotScript, IPProfile, Step45Output,
    new_project_id, new_shot_id, new_scene_id,
)
from manzhou.state_machine import ManzhouStateMachine, ProjectSession
from manzhou.schema_validator import SchemaValidator
from manzhou.prompt_builder import PromptBuilder
from manzhou.qwen_client import QwenClient


# =============================================================================
# 项目目录结构
# =============================================================================

def get_project_dirs(project_dir: str) -> dict:
    """返回标准项目目录路径"""
    p = Path(project_dir)
    return {
        "root":        str(p),
        "project_info": str(p / "00-项目信息"),
        "ip":          str(p / "01-IP档案"),
        "script":      str(p / "02-剧本"),
        "director":    str(p / "03-导演分析"),
        "storyboard":  str(p / "03-分镜"),
        "assets":      str(p / "05-资产库"),
        "session":     str(p / "09-状态机"),
    }


def ensure_dirs(dirs: dict) -> None:
    """确保所有目录存在"""
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)


# =============================================================================
# Step执行器（简化版，到Step 7截止）
# =============================================================================

class StepExecutor:
    """各Step的具体执行逻辑，到分镜脚本截止"""

    def __init__(self, session: ProjectSession, dirs: dict, episode: int):
        self.session = session
        self.dirs = dirs
        self.episode = episode
        # Schema 引擎（延迟初始化）
        self._validator: SchemaValidator | None = None
        self._prompt_builder: PromptBuilder | None = None

    # ------------------------------------------------------------------ Schema 引擎

    def _get_episode_name(self) -> str:
        """获取集数名称，如 '第1集'"""
        return f"第{self.episode}集"

    def _load_schema_engines(self) -> None:
        """
        加载 Schema 校验引擎（在 Step 7 执行前调用）
        读取 IP档案.yaml 和导演控制塔.md，初始化 validator 和 prompt_builder
        """
        ep_name = self._get_episode_name()

        # 读取 IP档案
        ip_path = os.path.join(self.dirs["ip"], "IP档案.yaml")
        ip_profile = None
        if os.path.exists(ip_path):
            try:
                with open(ip_path, "r", encoding="utf-8") as f:
                    ip_data = yaml.safe_load(f) or {}
                ip_profile = IPProfile(
                    project_id=ip_data.get("project_id", ""),
                    ip_profile_version=ip_data.get("version", "v10"),
                    ip_name=ip_data.get("ip_name", ""),
                    ip_type=ip_data.get("ip_type", ""),
                    characters={},
                    locations={},
                    items={},
                )
            except Exception as e:
                print(f"  ⚠️  IP档案读取失败: {e}")

        # 读取导演控制塔
        control_tower_path = os.path.join(
            self.dirs["director"], f"{ep_name}-导演控制塔.md"
        )
        step45_output = None
        if os.path.exists(control_tower_path):
            try:
                with open(control_tower_path, "r", encoding="utf-8") as f:
                    content = f.read()
                prohibited = ["美颜", "滤镜", "卡通化", "过度煽情"]
                for word in ["美颜", "滤镜", "卡通化", "煽情"]:
                    if word in content and word not in prohibited:
                        prohibited.append(word)
                step45_output = Step45Output(
                    project_id=self.session.project_id,
                    episode=ep_name,
                    emotion_baseline="虐/悲",
                    color_temp_range=("暖黄", "灰暗"),
                    emotion_curve=["L1", "L2", "L3", "L4", "L3", "L2", "L1"],
                    prohibited_keywords=prohibited,
                    shot_emotion_map={},
                    shot_camera_map={},
                )
            except Exception as e:
                print(f"  ⚠️  导演控制塔读取失败: {e}")

        if ip_profile and step45_output:
            self._validator = SchemaValidator(ip_profile, step45_output)
            self._prompt_builder = PromptBuilder(
                ip_profile, step45_output,
                style_preset="real", aspect_ratio="9:16"
            )
            print(f"  ✅ Schema 校验引擎已加载")
            print(f"  ✅ Prompt 构建器已加载")
            self.session.set_step_constraints(StepID.S7, {
                "required_fields": ["shots"],
                "char_id_pool": list(ip_profile.characters.keys()),
                "loc_id_pool": list(ip_profile.locations.keys()),
            })
        else:
            print(f"  ⚠️  Schema引擎初始化失败：IP档案={bool(ip_profile)}, 控制塔={bool(step45_output)}")

    # ------------------------------------------------------------------ Step 0: 项目配置

    def run_step_0(self, project_name: str, args: dict) -> tuple:
        """Step 0: 项目配置"""
        project_id = new_project_id()
        config = ProjectConfig(
            project_id=project_id,
            project_name=project_name,
            created_at=datetime.now().isoformat(),
            style_preset=args.get("style", "ShortDrama"),
            aspect_ratio=args.get("ratio", "9:16"),
            shot_duration=args.get("shot_duration", SHOT_DURATION_DEFAULT),
            target_episodes=args.get("episodes", 12),
            main_view_char=args.get("main_char", "char_01"),
            target_platform=args.get("platform", "抖音"),
            source_type=args.get("source_type", "file"),
            source_path=args.get("source_path", ""),
            word_count=args.get("word_count", 0),
        )

        output_path = os.path.join(self.dirs["project_info"], "项目配置单.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config.to_markdown())

        yaml_path = os.path.join(self.dirs["project_info"], "项目配置单.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config.__dict__, f, allow_unicode=True, default_flow_style=False)

        return True, output_path, {"project_id": project_id, "config_yaml": yaml_path}

    # ------------------------------------------------------------------ Step 7: 分镜脚本（自动生成结构骨架）

    def run_step_7(self) -> tuple:
        """
        Step 7: 分镜脚本生成（v10.0.0 Schema 驱动版）
        1. 加载 Schema 引擎
        2. 生成结构骨架（后续由人工填入 image_prompt / video_prompt）
        3. Schema 校验（人工填入后触发）
        """
        ep_name = self._get_episode_name()
        print(f"\n  📝 生成 {ep_name} 分镜脚本...")

        # Step 1: 加载 Schema 引擎
        self._load_schema_engines()

        # 读取导演控制塔
        director_path = os.path.join(
            self.dirs["director"],
            f"第{self.episode}集-导演控制塔.md"
        )
        control_tower_data = {}
        if os.path.exists(director_path):
            with open(director_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            control_tower_data = yaml.safe_load(parts[1]) or {}
                        except:
                            pass

        # 读取资产库
        asset_yaml = os.path.join(self.dirs["assets"], "资产库.yaml")
        asset_library = {}
        if os.path.exists(asset_yaml):
            with open(asset_yaml, "r", encoding="utf-8") as f:
                asset_library = yaml.safe_load(f) or {}

        total_duration = control_tower_data.get("total_duration", EPISODE_DURATION_DEFAULT)
        total_shots = total_duration // SHOT_DURATION_DEFAULT

        script_path = os.path.join(
            self.dirs["storyboard"],
            f"第{self.episode}集-分镜-v9.0.0.md"
        )

        header = f"""# 第{self.episode}集分镜脚本

> 生成时间: {datetime.now().isoformat()}
> 项目: {self.session.project_name}
> 版本: v9.0.0（简化版，到分镜截止）
> 总时长: {total_duration}秒
> 镜头数: {total_shots}
> 后续AI生成由人工执行

---

## 导演控制塔约束摘要

- 情绪类型: {control_tower_data.get('D1_emotion_baseline', {}).get('emotion_type', '待填写')}
- 色调: {control_tower_data.get('D1_emotion_baseline', {}).get('color_temp', '待填写')}
- 叙事节奏: {control_tower_data.get('D1_emotion_baseline', {}).get('narrative_pace', '待填写')}

---

## 后续执行（人工）

1. 上传角色参考图到LibTV
2. 逐镜填写 image_prompt → 生成图片
3. 逐镜填写 video_prompt → 生成视频
4. 下载所有视频片段
5. 剪映/FFmpeg拼接成片

---

## 分镜表

"""
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(header)

        print(f"  ✅ 分镜脚本已创建: {script_path}")

        # Step 3: Schema 校验（如果引擎已加载）
        if self._validator:
            print(f"  💡 Schema 校验引擎就绪")
            print(f"  💡 人工填入 image_prompt / video_prompt 后，可使用 SchemaValidator 校验")
        else:
            print(f"  💡 下一步：请在LibTV中填入每镜的image_prompt和video_prompt")

        return True, script_path, {
            "total_shots": total_shots,
            "total_duration": total_duration,
            "schema_validated": self._validator is not None,
        }


# =============================================================================
# CLI命令
# =============================================================================

def cmd_run(args) -> int:
    """manzhou run - 执行到分镜脚本截止"""
    project_dir = os.path.abspath(args.project)
    dirs = get_project_dirs(project_dir)
    ensure_dirs(dirs)

    print(f"\n{'#' * 60}")
    print(f"# 🎬 漫舟导演Agent v9.0.0（简化版）")
    print(f"# 项目: {args.project}")
    print(f"# 模式: {'断点恢复' if args.resume else '全新执行'}")
    print(f"{'#' * 60}\n")

    # 加载或创建会话
    session_path = os.path.join(dirs["session"], "session.json")
    if args.resume and os.path.exists(session_path):
        print("🔄 断点恢复模式")
        session = ProjectSession.load(session_path)
    else:
        project_name = os.path.basename(project_dir)
        session = ProjectSession(
            project_id=new_project_id(),
            project_name=project_name,
            episode=args.episode or "第1集",
            created_at=datetime.now().isoformat(),
        )

    sm = ManzhouStateMachine(session)
    executor = StepExecutor(
        session=session,
        dirs=dirs,
        episode=args.episode_number or 1,
    )

    # ------------------------------------------------------------------ Step 0: 项目配置

    sm.start_step(StepID.S0)
    success, output_ref, metadata = executor.run_step_0(
        project_name=session.project_name,
        args={
            "style": args.style or "ShortDrama",
            "ratio": args.ratio or "9:16",
            "shot_duration": args.shot_duration or SHOT_DURATION_DEFAULT,
            "episodes": args.episodes or 12,
            "main_char": args.main_char or "char_01",
            "platform": args.platform or "抖音",
        }
    )
    if success:
        sm.complete_step(StepID.S0, output_ref, metadata)
    else:
        sm.fail_step(StepID.S0, "Step 0失败")
        session.save(session_path)
        return 1

    # ------------------------------------------------------------------ Step 7: 分镜脚本

    sm.start_step(StepID.S7)
    success, output_ref, metadata = executor.run_step_7()
    if success:
        sm.complete_step(StepID.S7, output_ref, metadata)
    else:
        sm.fail_step(StepID.S7, "Step 7失败")
        session.save(session_path)
        return 1

    # 保存状态
    session.save(session_path)
    sm.print_status()

    print(f"\n✅ 执行完成！分镜脚本已生成")
    print(f"📁 会话状态: {session_path}")
    print(f"👤 后续AI生成由人工在LibTV执行")
    return 0


def cmd_status(args) -> int:
    """manzhou status - 查看项目状态"""
    project_dir = os.path.abspath(args.project)
    session_path = os.path.join(get_project_dirs(project_dir)["session"], "session.json")

    if not os.path.exists(session_path):
        print(f"❌ 未找到会话文件: {session_path}")
        return 1

    session = ProjectSession.load(session_path)
    sm = ManzhouStateMachine(session)
    sm.print_status()
    return 0


def cmd_generate(args) -> int:
    """manzhou generate - Qwen3-Max 自动生成每镜 Prompt"""
    project_dir = os.path.abspath(args.project)
    episode_num = args.episode or 1
    ep_name = f"第{episode_num}集"
    dirs = get_project_dirs(project_dir)

    print(f"\n{'#' * 60}")
    print(f"# 🎬 漫舟导演Agent v10.1.0 — Qwen3-Max Prompt生成")
    print(f"# 项目: {project_dir}")
    print(f"# 集数: {ep_name}")
    print(f"# 模型: qwen-max")
    print(f"{'#' * 60}\n")

    # 1. 查找分镜脚本（支持 第1集 / 第01集 两种格式）
    storyboard_dir = dirs["storyboard"]
    script_path = os.path.join(storyboard_dir, f"{ep_name}-分镜-v9.0.0.md")
    if not os.path.exists(script_path):
        # 尝试前导零格式
        alt_name = f"第{episode_num:02d}集"
        script_path = os.path.join(storyboard_dir, f"{alt_name}-分镜-v9.0.0.md")
        if not os.path.exists(script_path):
            # 列出可用文件
            available = [f for f in os.listdir(storyboard_dir) if "分镜" in f and f.endswith(".md")]
            print(f"❌ 分镜脚本不存在: {script_path}")
            if available:
                print(f"   可用文件: {available}")
            return 1

    with open(script_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    shots = _parse_shot_script(script_content)
    if not shots:
        print("❌ 未找到镜头信息")
        return 1
    print(f"  📋 解析到 {len(shots)} 个镜头")

    # 2. 解析 IP档案（角色+场景）
    ip_data = _parse_ip_profile(dirs["ip"])
    if not ip_data:
        print(f"❌ IP档案解析失败: {dirs['ip']}")
        return 1
    print(f"  📋 角色: {list(ip_data['characters'].keys())}")
    print(f"  📋 场景: {list(ip_data['locations'].keys())}")

    # 3. 解析导演控制塔（支持 第1集 / 第01集 格式）
    alt_name = f"第{episode_num:02d}集"
    control_tower_path = os.path.join(dirs["director"], f"{ep_name}-导演控制塔.md")
    if not os.path.exists(control_tower_path):
        control_tower_path = os.path.join(dirs["director"], f"{alt_name}-导演控制塔.md")
    step45_data = _parse_control_tower(control_tower_path, ip_data)

    # 4. 构建 Schema 对象
    ip_profile = IPProfile(
        project_id=ip_data.get("project_id", "unknown"),
        ip_profile_version="v10",
        ip_name=ip_data.get("ip_name", ""),
        ip_type=ip_data.get("ip_type", "现实主义"),
        characters=ip_data["characters"],
        locations=ip_data["locations"],
        items={},
    )
    step45_output = Step45Output(
        project_id=ip_data.get("project_id", "unknown"),
        episode=ep_name,
        emotion_baseline=step45_data.get("emotion_baseline", "虐/悲"),
        color_temp_range=step45_data.get("color_temp_range", ("暖黄", "灰暗")),
        emotion_curve=step45_data.get("emotion_curve", []),
        prohibited_keywords=step45_data.get("prohibited_keywords", ["美颜", "滤镜", "卡通化", "过度煽情"]),
        shot_emotion_map=step45_data.get("shot_emotion_map", {}),
        shot_camera_map=step45_data.get("shot_camera_map", {}),
    )

    # 5. 补全缺失的场景（shot script 中出现但 IP档案 中没有的）
    from manzhou.schema import IPLocation
    for shot in shots:
        loc_id = shot.get("location_id", "")
        if loc_id and loc_id not in ip_data["locations"]:
            print(f"  ⚠️  场景 \"{loc_id}\" 不在IP档案，创建fallback条目")
            ip_data["locations"][loc_id] = IPLocation(
                id=loc_id, name=loc_id, type="室外",
                time="白天", weather="晴", atmosphere="",
                color_temp="自然光", lighting="自然光",
                key_elements=[], visual_tags=[],
            )

    # 6. 初始化 Qwen + SchemaValidator
    api_key = os.getenv("DASHSCOPE_API_KEY") or args.api_key
    if not api_key:
        print("❌ 未设置 DASHSCOPE_API_KEY")
        print("   请运行: export DASHSCOPE_API_KEY='sk-...'")
        return 1

    qwen = QwenClient(api_key=api_key, model="qwen-max")
    validator = SchemaValidator(ip_profile, step45_output)
    print(f"  ✅ Qwen3-Max 已连接")

    # 6. 逐镜生成
    print(f"\n{'=' * 60}")
    print(f"开始生成 {len(shots)} 个镜头的 Prompt...")
    print(f"{'=' * 60}")

    results = []
    for i, shot in enumerate(shots):
        shot_id = shot["shot_id"]
        print(f"\n  [{i+1}/{len(shots)}] 镜头 {shot_id}...", end=" ", flush=True)

        # 构建上下文
        context = _build_shot_context(shot, ip_data, step45_data)
        system = _build_system_prompt(ip_data, step45_data)

        # 生成
        try:
            generated = qwen.generate_shot_prompts(system, context)
        except Exception as e:
            print(f"❌ API错误: {e}")
            results.append({**shot, "image_prompt": "", "video_prompt": "", "error": str(e)})
            continue

        img = generated.get("image_prompt", "")
        vid = generated.get("video_prompt", "")

        # 填入 shot 并校验
        shot_obj = _shot_dict_to_script(shot, img, vid)
        validation = validator.validate_shot(shot_obj)

        # 记录
        results.append({
            **shot,
            "image_prompt": img,
            "video_prompt": vid,
            "validation": validation,
        })

        # 打印结果
        if validation.is_passed:
            score = round(validation.d1_score * 0.35 + validation.d2_score * 0.35 + validation.d3_score * 0.30, 2)
            print(f"✅ D1={validation.d1_score:.1f} D2={validation.d2_score:.1f} D3={validation.d3_score:.1f} (综合{score})")
        else:
            blocks = [e for e in validation.errors if e.severity == "BLOCK"]
            print(f"❌ BLOCK: {[e.field for e in blocks]}")

    # 7. 更新分镜文件
    updated_content = _update_shot_script(script_content, results)
    basename = os.path.basename(script_path)
    output_path = script_path.replace("-v9.0.0.md", "-v10.1.0.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"\n  ✅ 更新分镜脚本: {output_path}")

    # 8. 汇总报告
    passed = sum(1 for r in results if r.get("validation") and r["validation"].is_passed)
    failed = len(results) - passed
    print(f"\n{'=' * 60}")
    print(f"📊 生成报告: 通过 {passed}/{len(results)}  失败 {failed}")
    print(f"{'=' * 60}")
    if failed > 0:
        print("❌ 失败镜头:")
        for r in results:
            if not r.get("validation") or not r["validation"].is_passed:
                sid = r.get("shot_id", "?")
                err = r.get("error", "")
                blocks = [e.field for e in r["validation"].errors if e.severity == "BLOCK"] if r.get("validation") else []
                reason = err or (f"BLOCK: {blocks}" if blocks else "未知")
                print(f"  - {sid}: {reason}")
    print()
    return 0


# =============================================================================
# 分镜脚本解析
# =============================================================================

def _parse_shot_script(content: str) -> list[dict]:
    """从 Markdown 分镜脚本解析镜头列表（分块提取）"""
    shots = []
    # 按 ## 镜N: 分割各镜头段落
    parts = re.split(r"\n(?=## 镜\d+:)", content)
    for part in parts:
        if "**分场内容**" not in part:
            continue
        shot = {"image_prompt": "", "video_prompt": ""}
        # shot_id + title
        m = re.search(r"## 镜\d+: (P\d+) \| ([^\n]+)", part)
        if m:
            shot["shot_id"] = m.group(1)
            shot["title"] = m.group(2).strip()
        # 分场内容
        m = re.search(r"\*\*分场内容\*\*: (.+?)(?=\n\n\*\*角色\*\*|\n\n\*\*)", part, re.DOTALL)
        if m:
            shot["script"] = m.group(1).strip()
        # 角色
        m = re.search(r"\*\*角色\*\*: (.+?)(?=\n)", part)
        if m:
            shot["character_ids"] = _parse_char_ids(m.group(1))
        # 场景
        m = re.search(r"\*\*场景\*\*: (.+?)(?=\n)", part)
        if m:
            shot["location_id"] = _parse_loc_id(m.group(1))
        # 情绪
        m = re.search(r"\*\*情绪\*\*: (.+?)(?=\n)", part)
        if m:
            shot["emotion_level"] = _parse_emotion(m.group(1))
        # 景别
        m = re.search(r"\*\*景别\*\*: (.+?)(?=\n)", part)
        if m:
            shot["shot_type"] = _parse_shot_type(m.group(1))
        # 运镜
        m = re.search(r"\*\*运镜\*\*: (.+?)(?=\n)", part)
        if m:
            shot["camera_action"] = _parse_camera_action(m.group(1))
        # 对白
        dialogues = re.findall(r"> 「([^」]+)」", part)
        shot["dialogue"] = " ".join(dialogues)
        # 现有 Prompt（code block）
        img_blocks = re.findall(r"\*\*Image Prompt\*\*.*?\n```\n?(.*?)\n?```", part, re.DOTALL)
        vid_blocks = re.findall(r"\*\*Video Prompt\*\*.*?\n```\n?(.*?)\n?```", part, re.DOTALL)
        if img_blocks:
            shot["image_prompt"] = img_blocks[0].strip()
        if vid_blocks:
            shot["video_prompt"] = vid_blocks[0].strip()
        if shot.get("shot_id"):
            shots.append(shot)
    return shots


def _parse_char_ids(text: str) -> list[str]:
    """解析角色ID列表"""
    ids = re.findall(r"char_\w+", text)
    return list(dict.fromkeys(ids))  # 去重保留顺序


def _parse_loc_id(text: str) -> str:
    """解析场景ID"""
    m = re.search(r"(loc_\w+)", text)
    return m.group(1) if m else text.strip()  # 返回原文（如"土路"）


def _parse_emotion(text: str) -> str:
    """解析情绪等级"""
    m = re.search(r"L(\d)", text)
    return f"L{m.group(1)}" if m else "L1"


def _parse_shot_type(text: str) -> str:
    """解析景别"""
    text = text.strip()
    m = re.search(r"(ECU|CU|MCU|MS|LS|WS|MWS)", text)
    return m.group(1) if m else "MS"


def _parse_camera_action(text: str) -> str:
    """解析运镜"""
    text = text.strip()
    if "固定" in text:
        return "固定"
    if "推进" in text:
        return "推进"
    if "拉远" in text:
        return "拉远"
    if "摇" in text:
        return "摇"
    if "跟拍" in text:
        return "跟拍"
    return "固定"


# =============================================================================
# IP档案解析
# =============================================================================

def _parse_ip_profile(ip_dir: str) -> dict:
    """解析 IP档案.yaml，返回 characters/locations 字典"""
    ip_path = os.path.join(ip_dir, "IP档案.yaml")
    if not os.path.exists(ip_path):
        return {}

    with open(ip_path, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "characters": {},
        "locations": {},
        "project_id": "unknown",
        "ip_name": "",
        "ip_type": "现实主义",
    }

    # 解析角色（提取年龄段数据，分割多阶段外貌/服装）
    char_pattern = re.compile(r"### (char_\w+)（(.+?)）")
    for m in char_pattern.finditer(content):
        char_id = m.group(1)
        char_name = m.group(2)
        start = m.start()
        next_char = char_pattern.search(content, m.end())
        end = next_char.start() if next_char else len(content)
        char_block = content[start:end]

        # 提取年龄段
        age_range = _extract_table_value(char_block, "年龄跨度", None) or _extract_table_value(char_block, "年龄", None) or ""
        # 提取外貌（可能有young/middle/old三段）
        raw_face = _extract_table_value(char_block, "外貌", "服装") or ""
        face_stages = _split_age_stages(raw_face)
        # 服装同样分割
        raw_clothing = _extract_table_value(char_block, "服装", "性格") or ""
        clothing_stages = _split_age_stages(raw_clothing)
        traits = _extract_table_value(char_block, "性格", "声音") or _extract_table_value(char_block, "性格", "标志性")

        from manzhou.schema import (
            IPCharacter, CharacterAppearance, CharacterClothing,
            CharacterPersonality, CharacterVoice, CharacterRelationship,
        )
        result["characters"][char_id] = IPCharacter(
            id=char_id, name=char_name, role_type="角色",
            age_range=age_range, aliases=[],
            appearance=CharacterAppearance(
                face=face_stages.get("young", raw_face[:50]),
                body="", distinguishing="", hair="",
            ),
            clothing=CharacterClothing(
                daily=clothing_stages.get("young", raw_clothing[:50]),
                work="", special="",
            ),
            personality=CharacterPersonality(
                traits=[traits] if traits else [],
                speech="", habits=[], conflict_style="",
            ),
            voice=CharacterVoice(timbre="", speed="", accent=""),
            relationships=[],
        )
        # 把完整多阶段数据存进对象的额外字段
        result["characters"][char_id]._age_range = age_range
        result["characters"][char_id]._face_stages = face_stages
        result["characters"][char_id]._clothing_stages = clothing_stages

    # 解析场景（5列表格: ID | 名称 | 时代氛围 | 光线 | 色调）
    loc_rows = re.findall(r"^\| (loc_\w+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", content, re.MULTILINE)
    for row in loc_rows:
        loc_id, loc_name, era, lighting, color = [s.strip() for s in row]
        from manzhou.schema import IPLocation
        result["locations"][loc_id] = IPLocation(
            id=loc_id, name=loc_name, type="",
            time=era, weather="晴", atmosphere="",
            color_temp=color, lighting=lighting,
            key_elements=[], visual_tags=[],
        )


    return result


def _extract_table_value(block: str, key1: str, key2: str) -> str:
    """从角色档案块中提取表格值"""
    pattern = re.compile(rf"\| {re.escape(key1)} \| ([^\|]+) \|")
    m = pattern.search(block)
    if m:
        val = m.group(1).strip()
        if key2:
            val = val.split(key2)[0].strip()
        return val
    return ""


def _split_age_stages(text: str) -> dict:
    """
    分割多年龄段描述，返回 {'young': ..., 'middle': ..., 'old': ...}
    支持 "年轻时xxx；中年xxx；老年xxx" 格式
    """
    if not text:
        return {}
    stages = {}
    # 匹配 "年轻时..." / "中年..." / "老年..."
    young_m = re.search(r"年轻时[：:]([^；;老年中年]+)", text)
    middle_m = re.search(r"中年[：:]?([^(老年年轻时)]+?)(?=老年|$)", text)
    old_m = re.search(r"老年[：:](.+)", text)
    if young_m:
        stages["young"] = young_m.group(1).strip()
    if middle_m:
        stages["middle"] = middle_m.group(1).strip()
    if old_m:
        stages["old"] = old_m.group(1).strip()
    return stages


def _select_age_stage(char_obj, script: str, shot_id: str, emotion: str) -> tuple:
    """
    根据镜头内容推断角色年龄段，返回 (face_desc, clothing_desc, stage_label)
    """
    # P02/P03 = 回忆少爷时期（年轻）
    if shot_id in ("P02", "P03"):
        stage = "young"
    # P01 = 老年末年叙事
    elif shot_id == "P01":
        stage = "old"
    else:
        # 关键词检测
        is_young = any(kw in script for kw in [
            "少爷", "绸衣", "一百亩", "骑", "丈人", "请安",
        ])
        is_old = any(kw in script for kw in [
            "老人", "干瘦", "老牛", "花白", "讲起",
        ])
        is_hardship = any(kw in script for kw in [
            "还债", "茅屋", "去世", "埋葬", "丧", "苦难",
        ])
        if is_old:
            stage = "old"
        elif is_young:
            stage = "young"
        elif is_hardship:
            stage = "middle"
        else:
            # 情绪推断：L4爆发/L3隐忍 → 中年
            stage = "middle" if emotion in ("L3", "L4") else "old"

    face = getattr(char_obj, "_face_stages", {}).get(stage, "")
    clothing = getattr(char_obj, "_clothing_stages", {}).get(stage, "")
    if not face:
        face = getattr(char_obj.appearance, "face", "") if hasattr(char_obj, "appearance") else ""
    if not clothing:
        clothing = getattr(char_obj.clothing, "daily", "") if hasattr(char_obj, "clothing") else ""

    stage_labels = {"young": "少爷时", "middle": "中年时", "old": "老年时"}
    return face, clothing, stage_labels.get(stage, stage)



# =============================================================================
# 导演控制塔解析
# =============================================================================

def _parse_control_tower(path: str, ip_data: dict) -> dict:
    """解析导演控制塔，提取约束"""
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    prohibited = ["美颜", "滤镜", "卡通化", "过度煽情"]
    for word in prohibited[:]:
        if word in content:
            pass
        for w in ["美颜", "滤镜", "卡通化", "煽情", "特效"]:
            if w in content and w not in prohibited:
                prohibited.append(w)

    # 解析情绪曲线
    emotion_map = {}
    emotion_pattern = re.compile(r"\| (P\d+) \| L(\d) \|")
    for m in emotion_pattern.finditer(content):
        emotion_map[m.group(1)] = f"L{m.group(2)}"

    # 解析景别运镜
    camera_map = {}
    cam_pattern = re.compile(r"\| (P\d+) \| (ECU|CU|MCU|MS|LS|WS) \| (固定|推进|拉远|摇|跟拍|缓慢推进)")
    for m in cam_pattern.finditer(content):
        camera_map[m.group(1)] = {"shot_type": m.group(2), "camera_action": m.group(3)}

    return {
        "emotion_baseline": "虐/悲",
        "color_temp_range": ("暖黄", "灰暗"),
        "emotion_curve": list(emotion_map.keys()),
        "prohibited_keywords": prohibited,
        "shot_emotion_map": emotion_map,
        "shot_camera_map": camera_map,
    }


# =============================================================================
# Prompt 构建
# =============================================================================

def _build_system_prompt(ip_data: dict, step45: dict) -> str:
    """构建 Qwen 系统提示"""
    chars = []
    for cid, char in ip_data.get("characters", {}).items():
        desc = f"  - {cid}（{char.name}）"
        if char.appearance and char.appearance.face:
            desc += f": {char.appearance.face}"
        if char.clothing and char.clothing.daily:
            desc += f", 服装: {char.clothing.daily}"
        chars.append(desc)
    chars_text = "\n".join(chars) if chars else "（无角色档案）"

    locs = []
    for lid, loc in ip_data.get("locations", {}).items():
        color = loc.color_temp if loc.color_temp else ""
        locs.append(f"  - {lid}（{loc.name}）{color}")
    locs_text = "\n".join(locs) if locs else "（无场景档案）"

    prohibited = " ".join(step45.get("prohibited_keywords", ["美颜", "滤镜", "卡通化"]))

    return f"""你是漫舟AI漫剧的Prompt生成专家。

【角色档案】
{chars_text}

【场景档案】
{locs_text}

【本集禁止词】（严禁出现）
{prohibited}

【情绪等级说明】
L1=平静 L2=克制 L3=隐忍 L4=爆发 L5=高潮

【情绪跳转规则】
L1→L2/L3 ✓  L1→L4 ✗  L4→L1 ✗  L3→L5 ✗

【输出格式】
严格按以下格式输出，不要解释，不要给建议：
IMAGE: <画面描述（写实摄影风格，30-100字，不含禁止词）>
VIDEO: <运镜描述（10-50字，不含禁止词）>"""


def _build_shot_context(shot: dict, ip_data: dict, step45: dict) -> str:
    """为单个镜头构建上下文（年龄段感知）"""
    char_names = []
    for cid in shot.get("character_ids", []):
        char = ip_data.get("characters", {}).get(cid)
        if char:
            script = shot.get("script", "")
            shot_id = shot.get("shot_id", "P01")
            emotion = shot.get("emotion_level", "L1")
            face, clothing, stage_label = _select_age_stage(char, script, shot_id, emotion)
            age_range = getattr(char, "_age_range", "") or char.age_range
            parts = [f"{char.name}({stage_label})"]
            if face:
                parts.append(f"外貌:{face}")
            if clothing:
                parts.append(f"服装:{clothing}")
            if age_range and age_range != getattr(char, "_age_range", ""):
                parts.append(f"年龄跨度:{age_range}")
            char_names.append("，".join(parts))
        else:
            char_names.append(cid)

    loc = ip_data.get("locations", {}).get(shot.get("location_id", ""))
    loc_desc = f"{loc.name}，色调{loc.color_temp}，光线{loc.lighting}" if loc else shot.get("location_id", "")

    emotion = shot.get("emotion_level", "L1")
    shot_type = shot.get("shot_type", "MS")
    camera = shot.get("camera_action", "固定")

    prohibited = " ".join(step45.get("prohibited_keywords", []))

    return f"""【镜头 {shot.get("shot_id","")}】

角色：{'；'.join(char_names)}
场景：{loc_desc}
分场内容：{shot.get("script","")}
情绪：{emotion}
景别：{shot_type}
运镜：{camera}
对白：{shot.get("dialogue","")}

禁止词：{prohibited}

请生成符合以上约束的IMAGE和VIDEO Prompt。"""


def _shot_dict_to_script(shot: dict, img: str, vid: str):
    """将 dict 转成 ShotScript dataclass"""
    from manzhou.schema import ShotScript
    return ShotScript(
        shot_id=shot.get("shot_id", "P01"),
        duration_sec=8,
        location_id=shot.get("location_id", ""),
        character_ids=shot.get("character_ids", []),
        script=shot.get("script", ""),
        dialogue=shot.get("dialogue", ""),
        image_prompt=img,
        video_prompt=vid,
        emotion_level=shot.get("emotion_level", "L1"),
        beat_position=shot.get("beat_position", "B01"),
        shot_type=shot.get("shot_type", "MS"),
        camera_action=shot.get("camera_action", "固定"),
    )


def _update_shot_script(original: str, results: list[dict]) -> str:
    """用生成结果更新分镜脚本"""
    content = original

    # 更新 header 版本
    content = content.replace("v9.0.0", "v10.1.0")
    content = content.replace("后续AI生成由人工执行", "Qwen3-Max 自动生成 + Schema校验")

    # 更新每个镜头的 Prompt
    for r in results:
        shot_id = r.get("shot_id", "")
        img = r.get("image_prompt", "")
        vid = r.get("video_prompt", "")

        # 找该镜头段落
        pattern = re.compile(
            rf"(## 镜\d+: {re.escape(shot_id)} \| .+?\n)(.+?)(?=\n---\n## 镜|\n---\n\n## 后续|\n---\n\n\*\*)",
            re.DOTALL
        )

        def replace_shot(m):
            header = m.group(1)
            body = m.group(2)
            # 替换 Image Prompt
            body = re.sub(
                r"(\*\*Image Prompt\*\*.*?\n)```[\s\S]*?```",
                lambda xm: xm.group(1) + f"```\n{img}\n```",
                body,
                flags=re.DOTALL
            )
            # 替换 Video Prompt
            body = re.sub(
                r"(\*\*Video Prompt\*\*.*?\n)```[\s\S]*?```",
                lambda xm: xm.group(1) + f"```\n{vid}\n```",
                body,
                flags=re.DOTALL
            )
            return header + body

        content = pattern.sub(replace_shot, content, count=1)

    # 添加校验报告
    passed = sum(1 for r in results if r.get("validation") and r["validation"].is_passed)
    failed = len(results) - passed
    report = f"""
---

## Qwen3-Max 生成报告

| 镜头 | 状态 | D1 | D2 | D3 |
|------|------|----|----|-----|
"""
    for r in results:
        v = r.get("validation")
        sid = r.get("shot_id", "?")
        if v:
            ok = "✅" if v.is_passed else "❌"
            report += f"| {sid} | {ok} | {v.d1_score:.1f} | {v.d2_score:.1f} | {v.d3_score:.1f} |\n"
        else:
            report += f"| {sid} | ❌ | - | - | - |\n"

    report += f"\n**通过率**: {passed}/{len(results)}  **{'全部通过' if failed == 0 else f'失败{failed}个'}**\n"
    content += report

    return content


def main():
    parser = argparse.ArgumentParser(
        description="漫舟导演Agent v10.1.0 - AI漫剧分镜脚本生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  manzhou run ./活着              # 全新执行到分镜
  manzhou run ./活着 --resume      # 断点恢复
  manzhou generate ./活着          # Qwen3-Max生成Prompt
  manzhou generate ./活着 --episode 2  # 生成第2集
  manzhou status ./活着            # 查看状态

流程:
  Step 0 → Step 7（分镜脚本）
  generate → Qwen3-Max自动生成Prompt + Schema校验
        """
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run命令
    run_parser = sub.add_parser("run", help="运行制作流程（到分镜截止）")
    run_parser.add_argument("project", help="项目目录路径")
    run_parser.add_argument("--resume", action="store_true", help="从断点恢复")
    run_parser.add_argument("--episode", type=str, default=None, help="集数名称")
    run_parser.add_argument("--episode-number", type=int, default=1, help="集数编号")
    run_parser.add_argument("--style", default="ShortDrama", help=f"风格预设")
    run_parser.add_argument("--ratio", default="9:16", help="画幅比例")
    run_parser.add_argument("--shot-duration", type=int, default=SHOT_DURATION_DEFAULT, help="单镜头时长")
    run_parser.add_argument("--episodes", type=int, default=12, help="目标集数")
    run_parser.add_argument("--main-char", default="char_01", help="主视角角色")
    run_parser.add_argument("--platform", default="抖音", help="目标平台")
    run_parser.set_defaults(func=cmd_run)

    # status命令
    status_parser = sub.add_parser("status", help="查看项目状态")
    status_parser.add_argument("project", help="项目目录路径")
    status_parser.set_defaults(func=cmd_status)

    # generate命令
    gen_parser = sub.add_parser("generate", help="Qwen3-Max 自动生成每镜 Prompt")
    gen_parser.add_argument("project", help="项目目录路径")
    gen_parser.add_argument("--episode", type=int, default=1, help="集数编号（默认1）")
    gen_parser.add_argument("--api-key", dest="api_key", default=None, help="DASHSCOPE_API_KEY（默认从环境变量读取）")
    gen_parser.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
