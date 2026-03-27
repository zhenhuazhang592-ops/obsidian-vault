#!/usr/bin/env python3
"""
漫舟CDP Agent · 交互式漫剧文档生成器
原封不动照搬联易方舟六步流程，每步与用户交互确认

使用方法：
    python cdp_doc_generator_interactive.py

版本: v2.0.0
日期: 2026-03-27
"""

import argparse
import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# 常量定义
# ============================================================================

STYLE_PRESETS = {
    "anime": "日漫风格：清晰线稿、赛璐璐上色、表情夸张可爱",
    "cn_anime": "国风动漫：国风美术与动画质感结合，色彩典雅",
    "cn_3d": "国风3D：国风符号+3D质感，史诗氛围",
    "ink": "水墨国风：水墨写意、留白、宣纸纹理",
    "cyber": "赛博朋克：霓虹光效，未来都市",
    "us_comics": "美漫风格：强轮廓线、高对比上色",
    "real": "写实风格：真实摄影质感",
    "horror": "恐怖惊悚：低照度、高反差",
    "pixar": "皮克斯风格：美式3D动画感",
    "shinkai": "新海诚风格：通透光影动画感",
    "miyazaki": "宫崎骏风格：治愈手绘动画风"
}

PLATFORMS = {
    "douyin": "抖音",
    "kuaishou": "快手",
    "wechat": "视频号",
    "bilibili": "B站"
}

ASPECT_RATIOS = {
    "9:16": "竖屏短视频（推荐）",
    "16:9": "横屏长视频",
    "3:4": "3:4方屏",
    "1:1": "1:1方图"
}

SHOT_DURATIONS = {
    "8": "8秒（适合快节奏）",
    "10": "10秒（标准）",
    "15": "15秒（叙事丰富）",
    "25": "25秒（长镜头）"
}


# ============================================================================
# 用户交互模块
# ============================================================================

class InteractivePrompt:
    """交互式问答"""

    @staticmethod
    def print_header(title: str):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    @staticmethod
    def print_step(step: int, total: int, title: str):
        """打印步骤标题"""
        print("\n" + "=" * 60)
        print(f"  步骤 {step}/{total}: {title}")
        print("=" * 60)

    @staticmethod
    def confirm(prompt: str, default: bool = True) -> bool:
        """确认问答"""
        suffix = " [Y/n]" if default else " [y/N]"
        while True:
            response = input(f"  {prompt}{suffix}: ").strip().lower()
            if not response:
                return default
            if response in ('y', 'yes', '是', '确认'):
                return True
            if response in ('n', 'no', '否', '取消'):
                return False
            print("  请输入 y 或 n")

    @staticmethod
    def choose(prompt: str, options: Dict[str, str], default: str = None) -> str:
        """选择问答"""
        print(f"\n  {prompt}")
        print("  " + "-" * 40)

        items = list(options.items())
        for i, (key, desc) in enumerate(items, 1):
            marker = " ← 默认" if key == default else ""
            print(f"    {i}. {desc} {marker}")

        print("  " + "-" * 40)

        while True:
            response = input(f"  请选择 (1-{len(items)})").strip()
            if not response and default:
                return default
            try:
                idx = int(response) - 1
                if 0 <= idx < len(items):
                    return items[idx][0]
            except ValueError:
                pass
            print(f"  请输入 1-{len(items)} 的数字")

    @classmethod
    def input_text(cls, prompt: str, default: str = "", required: bool = False, max_attempts: int = 3) -> str:
        """文本输入"""
        suffix = f" [{default}]" if default else ""
        suffix += " (必填)" if required else ""
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            try:
                response = input(f"  {prompt}{suffix}: ").strip()
                if response:
                    return response
                if default:
                    return default
                if not required:
                    return ""
                if attempts < max_attempts:
                    cls.print_warning(f"此项为必填，请输入内容 (剩余{max_attempts - attempts}次)")
            except EOFError:
                return default if default else ""
        return default if default else ""

    @staticmethod
    def input_multiline(prompt: str) -> str:
        """多行文本输入"""
        print(f"\n  {prompt}")
        print("  (输入空行结束，按 Enter 两次)")
        print("  " + "-" * 40)
        lines = []
        empty_count = 0
        while True:
            line = input()
            if not line.strip():
                empty_count += 1
                if empty_count >= 1:
                    break
            else:
                empty_count = 0
                lines.append(line.strip())
        return "\n".join(lines)

    @staticmethod
    def select_from_list(prompt: str, items: List[str], multi: bool = False) -> List[str]:
        """从列表中选择"""
        print(f"\n  {prompt}")
        print("  (输入编号，多选用逗号分隔，如: 1,3,5)")
        if not multi:
            print("  (输入 all 全选)")
        print("  " + "-" * 40)

        for i, item in enumerate(items, 1):
            print(f"    {i}. {item}")

        print("  " + "-" * 40)

        while True:
            response = input("  请选择: ").strip()
            if not response:
                continue

            if response.lower() == 'all':
                return items

            try:
                if ',' in response:
                    indices = [int(x.strip()) - 1 for x in response.split(',')]
                else:
                    indices = [int(response) - 1]

                selected = [items[i] for i in indices if 0 <= i < len(items)]
                if selected:
                    return selected
            except ValueError:
                pass
            print("  输入无效，请重新选择")

    @staticmethod
    def print_success(msg: str):
        print(f"  ✅ {msg}")

    @staticmethod
    def print_info(msg: str):
        print(f"  ℹ️  {msg}")

    @staticmethod
    def print_warning(msg: str):
        print(f"  ⚠️  {msg}")

    @staticmethod
    def print_error(msg: str):
        print(f"  ❌ {msg}")


# ============================================================================
# 步骤1：全局设置
# ============================================================================

class Step1GlobalSettings:
    """步骤1：全局设置"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self) -> Dict:
        self.p.print_step(1, 6, "全局设置")

        settings = {}

        # 项目名称
        settings['project_name'] = self.p.input_text(
            "项目名称",
            required=True
        )

        # 原作
        settings['author'] = self.p.input_text(
            "原作/作者",
            default="余华"
        )

        # 风格预设
        settings['style_preset'] = self.p.choose(
            "请选择视觉风格",
            STYLE_PRESETS,
            default="real"
        )

        # 画幅
        settings['aspect_ratio'] = self.p.choose(
            "请选择画幅比例",
            ASPECT_RATIOS,
            default="9:16"
        )

        # 目标平台
        settings['target_platform'] = self.p.choose(
            "请选择目标平台",
            PLATFORMS,
            default="douyin"
        )

        # 单镜头时长
        settings['shot_duration'] = self.p.choose(
            "请选择单镜头时长",
            SHOT_DURATIONS,
            default="8"
        )

        # 每集时长
        settings['episode_duration'] = self.p.input_text(
            "每集目标时长（分钟）",
            default="2"
        )

        # 预览设置
        self.p.print_info(f"\n项目配置预览：")
        print(f"""
  项目名称: {settings['project_name']}
  原作: {settings['author']}
  风格: {STYLE_PRESETS[settings['style_preset']]}
  画幅: {settings['aspect_ratio']}
  目标平台: {PLATFORMS[settings['target_platform']]}
  单镜头时长: {settings['shot_duration']}秒
  每集时长: {settings['episode_duration']}分钟
""")

        # 确认
        if self.p.confirm("确认以上配置？"):
            self.p.print_success("全局设置已完成")
            return settings
        else:
            self.p.print_warning("配置已取消，重新执行步骤1")
            return self.run()


# ============================================================================
# 步骤2：故事脚本（导入小说/输入CDP JSON）
# ============================================================================

class Step2StoryScript:
    """步骤2：故事脚本"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self, global_settings: Dict) -> Dict:
        self.p.print_step(2, 6, "故事脚本")

        self.p.print_info("请选择输入方式：")

        mode = self.p.choose(
            "故事脚本输入方式",
            {
                "cdp_json": "导入CDP JSON文件（已完成改编）",
                "novel": "导入小说TXT/DOCX（需要AI改编）",
                "manual": "手动输入剧本内容"
            },
            default="cdp_json"
        )

        if mode == "cdp_json":
            return self._import_cdp_json()
        elif mode == "novel":
            return self._import_novel()
        else:
            return self._manual_input()

    def _import_cdp_json(self) -> Dict:
        """导入CDP JSON"""
        filepath = self.p.input_text(
            "CDP JSON文件路径",
            required=True
        )

        if not os.path.exists(filepath):
            self.p.print_error(f"文件不存在: {filepath}")
            return self._import_cdp_json()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析JSON
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            self.p.print_error(f"JSON解析失败: {e}")
            return self._import_cdp_json()

        # 预览统计
        characters = data.get("characters", [])
        locations = data.get("locations", [])
        shots = data.get("shots", [])

        self.p.print_success(f"CDP JSON解析成功！")
        print(f"""
  角色数量: {len(characters)}
  场景数量: {len(locations)}
  道具数量: {len(data.get('items', []))}
  镜头数量: {len(shots)}
  总时长: {sum(s.get('durationSec', 8) for s in shots)}秒
""")

        # 确认
        if self.p.confirm("确认导入此CDP JSON？"):
            return data
        else:
            return self._import_cdp_json()

    def _import_novel(self) -> Dict:
        """导入小说"""
        filepath = self.p.input_text(
            "小说文件路径（TXT/DOCX）",
            required=True
        )

        if not os.path.exists(filepath):
            self.p.print_error(f"文件不存在: {filepath}")
            return self._import_novel()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        word_count = len(content)
        self.p.print_success(f"小说导入成功！")
        self.p.print_info(f"字数统计: {word_count}字")

        # TODO: 调用AI改编（这里先标记为待实现）
        self.p.print_warning("AI改编功能待实现，当前版本请直接提供CDP JSON")

        return {"raw_novel": content, "word_count": word_count}

    def _manual_input(self) -> Dict:
        """手动输入"""
        self.p.print_info("请按提示手动输入剧本信息")

        cdp_data = {
            "title": self.p.input_text("项目标题", required=True),
            "characters": [],
            "locations": [],
            "items": [],
            "shots": []
        }

        # 角色
        self.p.print_info("\n--- 角色信息 ---")
        if self.p.confirm("添加角色？"):
            while True:
                char = {
                    "id": f"c_c{len(cdp_data['characters']) + 1}",
                    "name": self.p.input_text("角色名称", required=True),
                    "aliases": self.p.input_text("别名（逗号分隔）").split(","),
                    "gender": self.p.choose("性别", {"male": "男", "female": "女"}),
                    "age": self.p.input_text("年龄"),
                    "appearance": self.p.input_text("外貌描述"),
                    "clothing": self.p.input_text("穿着描述"),
                    "persona": self.p.input_text("性格描述")
                }
                cdp_data["characters"].append(char)

                if not self.p.confirm("继续添加角色？", default=False):
                    break

        # 场景
        self.p.print_info("\n--- 场景信息 ---")
        if self.p.confirm("添加场景？"):
            while True:
                loc = {
                    "id": f"l_l{len(cdp_data['locations']) + 1}",
                    "name": self.p.input_text("场景名称", required=True),
                    "description": self.p.input_text("场景描述"),
                    "props": self.p.input_text("道具（逗号分隔）").split(",")
                }
                cdp_data["locations"].append(loc)

                if not self.p.confirm("继续添加场景？", default=False):
                    break

        # 镜头
        self.p.print_info("\n--- 镜头信息 ---")
        if self.p.confirm("添加镜头？"):
            while True:
                shot_num = len(cdp_data["shots"]) + 1
                self.p.print_info(f"\n--- 镜头 {shot_num} ---")

                loc_id = self.p.choose(
                    "选择场景",
                    {loc["id"]: f"{loc['name']} ({loc['id']})"
                        for loc in cdp_data["locations"]}
                ) if cdp_data["locations"] else None

                char_ids = []
                if cdp_data["characters"]:
                    selected = self.p.select_from_list(
                        "选择角色（可多选）",
                        [f"{c['id']} {c['name']}" for c in cdp_data["characters"]],
                        multi=True
                    )
                    char_ids = [c.split()[0] for c in selected]

                dialogue_text = self.p.input_text("对白内容")
                dialogues = []
                if dialogue_text and char_ids:
                    for cid in char_ids:
                        dialogues.append({"speakerId": cid, "text": dialogue_text})

                shot = {
                    "id": f"sh_sh{shot_num}",
                    "shotNumber": shot_num,
                    "durationSec": 8,
                    "locationId": loc_id,
                    "characterIds": char_ids,
                    "itemIds": [],
                    "script": self.p.input_text("镜头叙事"),
                    "dialogue": dialogues,
                    "imagePrompt": self.p.input_text("AI生图Prompt"),
                    "videoPrompt": self.p.input_text("AI视频Prompt"),
                    "objective": self.p.input_text("镜头目标"),
                    "action": {
                        "0-4s": self.p.input_text("0-4秒动作"),
                        "4-6s": self.p.input_text("4-6秒动作"),
                        "6-8s": self.p.input_text("6-8秒动作")
                    }
                }
                cdp_data["shots"].append(shot)

                if not self.p.confirm("继续添加镜头？", default=False):
                    break

        self.p.print_success(f"手动输入完成！")
        self.p.print_info(f"角色: {len(cdp_data['characters'])} | 场景: {len(cdp_data['locations'])} | 镜头: {len(cdp_data['shots'])}")

        return cdp_data


# ============================================================================
# 步骤3：资产库
# ============================================================================

class Step3AssetLibrary:
    """步骤3：资产库管理"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self, cdp_data: Dict) -> Dict:
        self.p.print_step(3, 6, "资产库管理")

        # 显示资产概览
        characters = cdp_data.get("characters", [])
        locations = cdp_data.get("locations", [])
        items = cdp_data.get("items", [])

        self.p.print_info("资产概览：")
        print(f"""
  角色资产: {len(characters)} 个
  场景资产: {len(locations)} 个
  道具资产: {len(items)} 个
""")

        # 详细查看
        if self.p.confirm("查看角色详情？"):
            for char in characters:
                print(f"\n  [{char.get('id')}] {char.get('name')}")
                print(f"    别名: {', '.join(char.get('aliases', []))}")
                print(f"    外貌: {char.get('appearance', '')[:50]}...")
                print(f"    穿着: {char.get('clothing', '')[:50]}...")

        if self.p.confirm("查看场景详情？"):
            for loc in locations:
                print(f"\n  [{loc.get('id')}] {loc.get('name')}")
                print(f"    描述: {loc.get('description', '')[:50]}...")
                print(f"    道具: {', '.join(loc.get('props', []))}")

        # 生成任务
        self.p.print_info("\n生成任务：")
        print(f"""
  ⬜ 角色图生成: {len(characters)} 张
  ⬜ 场景图生成: {len(locations)} 张
  ⬜ 道具图生成: {len(items)} 张
""")

        # 生成工具选择
        generation_tool = self.p.choose(
            "请选择生成工具",
            {
                "libtv": "LibTV（推荐，集成度高）",
                "seedance": "Seedance（质量好）",
                "midjourney": "Midjourney（细节丰富）",
                "manual": "手动生成（我会在其他地方生成）"
            },
            default="libtv"
        )

        # 保存配置
        asset_config = {
            "generation_tool": generation_tool,
            "character_count": len(characters),
            "location_count": len(locations),
            "item_count": len(items),
            "pending_tasks": {
                "characters": [char.get("id") for char in characters],
                "locations": [loc.get("id") for loc in locations],
                "items": [item.get("id") for item in items]
            }
        }

        if generation_tool == "manual":
            self.p.print_info("已记录生成任务，请稍后手动生成资产图")
        else:
            self.p.print_info(f"将在后续生成任务清单中提供 {generation_tool} 的使用指引")

        # 确认
        if self.p.confirm("确认资产库配置？"):
            self.p.print_success("资产库配置已完成")
            return asset_config
        else:
            return self.run(cdp_data)


# ============================================================================
# 步骤4：分镜脚本
# ============================================================================

class Step4Storyboard:
    """步骤4：分镜脚本"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self, cdp_data: Dict, asset_config: Dict) -> Dict:
        self.p.print_step(4, 6, "分镜脚本")

        shots = cdp_data.get("shots", [])
        self.p.print_info(f"共 {len(shots)} 个镜头")

        # 显示镜头列表
        print("\n  镜头列表：")
        print("  " + "-" * 50)
        for shot in shots[:10]:  # 只显示前10个
            duration = shot.get("durationSec", 8)
            loc_id = shot.get("locationId", "")
            char_ids = shot.get("characterIds", [])
            print(f"    P{shot.get('shotNumber', ''):02d} | {duration}s | 场景:{loc_id} | 角色:{','.join(char_ids)}")

        if len(shots) > 10:
            print(f"    ... 还有 {len(shots) - 10} 个镜头")

        print("  " + "-" * 50)

        # 编辑选项
        if self.p.confirm("需要编辑/调整镜头？"):
            return self._edit_shots(cdp_data)
        else:
            # 生成九宫格分镜
            nine_grid_enabled = self.p.confirm("是否生成九宫格分镜Prompt？")

            storyboard_config = {
                "total_shots": len(shots),
                "nine_grid_enabled": nine_grid_enabled,
                "shot_preview": shots[:5]  # 保存前5个预览
            }

            self.p.print_success("分镜脚本确认完成")
            return storyboard_config

    def _edit_shots(self, cdp_data: Dict) -> Dict:
        """编辑镜头"""
        shots = cdp_data.get("shots", [])

        while True:
            print("\n  可编辑选项：")
            print("    1. 编辑单个镜头")
            print("    2. 批量修改时长")
            print("    3. 删除镜头")
            print("    4. 添加镜头")
            print("    0. 完成编辑")

            choice = input("  请选择: ").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._edit_single_shot(shots)
            elif choice == "2":
                self._batch_edit_duration(shots)
            elif choice == "3":
                self._delete_shot(shots)
            elif choice == "4":
                self._add_shot(shots)

        self.p.print_success("镜头编辑完成")
        return {"total_shots": len(shots), "edited": True}

    def _edit_single_shot(self, shots: List):
        """编辑单个镜头"""
        for i, shot in enumerate(shots, 1):
            print(f"  {i}. P{shot.get('shotNumber', i):02d} | {shot.get('script', '')[:30]}...")

        idx = input("  选择镜头编号: ").strip()
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(shots):
                shot = shots[idx]
                print(f"\n  编辑镜头 P{shot.get('shotNumber', idx+1):02d}")
                shot['script'] = self.p.input_text("镜头叙事", default=shot.get('script', ''))
                shot['durationSec'] = int(self.p.input_text("时长(秒)", default=str(shot.get('durationSec', 8))))

                # 对白
                print("  当前对白:")
                for d in shot.get('dialogue', []):
                    print(f"    {d.get('speakerId')}: {d.get('text', '')}")

                if self.p.confirm("添加对白？"):
                    speaker = self.p.input_text("说话者ID")
                    text = self.p.input_text("对白内容")
                    shot.setdefault('dialogue', []).append({"speakerId": speaker, "text": text})

                self.p.print_success("镜头已更新")
        except ValueError:
            self.p.print_error("无效选择")

    def _batch_edit_duration(self, shots: List):
        """批量修改时长"""
        new_duration = int(self.p.input_text("新时长(秒)"))
        for shot in shots:
            shot['durationSec'] = new_duration
        self.p.print_success(f"所有镜头时长已修改为 {new_duration} 秒")

    def _delete_shot(self, shots: List):
        """删除镜头"""
        for i, shot in enumerate(shots, 1):
            print(f"  {i}. P{shot.get('shotNumber', i):02d} | {shot.get('script', '')[:30]}...")

        idx = input("  选择要删除的镜头编号 (输入多个用逗号分隔): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in idx.split(',')]
            indices.sort(reverse=True)
            for i in indices:
                if 0 <= i < len(shots):
                    shots.pop(i)
            self.p.print_success(f"已删除 {len(indices)} 个镜头")
        except ValueError:
            self.p.print_error("无效选择")

    def _add_shot(self, shots: List):
        """添加镜头"""
        shot_num = len(shots) + 1
        new_shot = {
            "id": f"sh_sh{shot_num}",
            "shotNumber": shot_num,
            "durationSec": 8,
            "locationId": "",
            "characterIds": [],
            "script": self.p.input_text("镜头叙事", required=True),
            "dialogue": [],
            "imagePrompt": "",
            "videoPrompt": "",
            "objective": ""
        }
        shots.append(new_shot)
        self.p.print_success(f"已添加镜头 P{shot_num:02d}")


# ============================================================================
# 步骤5：分镜视频
# ============================================================================

class Step5VideoGeneration:
    """步骤5：分镜视频"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self, cdp_data: Dict) -> Dict:
        self.p.print_step(5, 6, "分镜视频")

        shots = cdp_data.get("shots", [])
        self.p.print_info(f"共 {len(shots)} 个镜头需要生成视频")

        # 视频模型选择
        video_model = self.p.choose(
            "请选择视频生成模型",
            {
                "kling": "可灵Kling（推荐，质量好）",
                "seedance": "Seedance（性价比高）",
                "runway": "Runway（创意丰富）",
                "libtv": "LibTV Canvas（集成操作）"
            },
            default="kling"
        )

        # 创作模式
        creation_mode = self.p.choose(
            "创作模式",
            {
                "img2video": "图生视频（先生成分镜图，再生成视频）",
                "text2video": "文生视频（直接生成）"
            },
            default="img2video"
        )

        # 生成策略
        generation_strategy = self.p.choose(
            "生成策略",
            {
                "batch": "批量生成（全部一起生成）",
                "sequential": "逐个生成（生成完一个再下一个）"
            },
            default="batch"
        )

        video_config = {
            "model": video_model,
            "creation_mode": creation_mode,
            "strategy": generation_strategy,
            "total_shots": len(shots),
            "video_prompts": [shot.get("videoPrompt", "") for shot in shots]
        }

        # 显示任务清单预览
        self.p.print_info("\n视频生成任务预览：")
        print("  " + "-" * 50)
        for shot in shots[:5]:
            print(f"    P{shot.get('shotNumber', ''):02d} | {shot.get('durationSec', 8)}s | {shot.get('videoPrompt', '')[:30]}...")
        if len(shots) > 5:
            print(f"    ... 还有 {len(shots) - 5} 个镜头")
        print("  " + "-" * 50)

        # 导出格式
        export_format = self.p.choose(
            "导出格式",
            {
                "jianying": "剪映工程文件（推荐）",
                "zip": "ZIP压缩包",
                "folder": "文件夹（直接保存视频文件）"
            },
            default="jianying"
        )

        video_config["export_format"] = export_format

        # 确认
        if self.p.confirm("确认视频生成配置？"):
            self.p.print_success("视频生成配置已完成")
            return video_config
        else:
            return self.run(cdp_data)


# ============================================================================
# 步骤6：导出配置单
# ============================================================================

class Step6Export:
    """步骤6：导出配置单"""

    def __init__(self, interactive: InteractivePrompt):
        self.p = interactive

    def run(self,
            global_settings: Dict,
            cdp_data: Dict,
            asset_config: Dict,
            storyboard_config: Dict,
            video_config: Dict) -> Dict:
        self.p.print_step(6, 6, "导出配置单")

        # 输出目录
        output_dir = self.p.input_text(
            "输出目录",
            default="./cdp_output"
        )

        # 项目名称
        project_name = global_settings.get("project_name", "未命名项目")
        project_dir = os.path.join(output_dir, project_name)

        # 确认项目信息
        self.p.print_info("\n项目信息汇总：")
        print(f"""
  项目名称: {project_name}
  原作: {global_settings.get('author', '')}
  风格: {STYLE_PRESETS.get(global_settings.get('style_preset', 'anime'))}
  画幅: {global_settings.get('aspect_ratio', '9:16')}
  目标平台: {PLATFORMS.get(global_settings.get('target_platform', 'douyin'))}

  角色: {asset_config.get('character_count', 0)} 个
  场景: {asset_config.get('location_count', 0)} 个
  道具: {asset_config.get('item_count', 0)} 个
  镜头: {storyboard_config.get('total_shots', 0)} 个

  视频模型: {video_config.get('model', 'kling')}
  创作模式: {video_config.get('creation_mode', 'img2video')}
  导出格式: {video_config.get('export_format', 'jianying')}
""")

        # 导出内容选择
        self.p.print_info("\n导出内容：")
        export_items = {
            "project_config": self.p.confirm("项目配置单", True),
            "cdp_json": self.p.confirm("CDP JSON原始数据", True),
            "asset_library": self.p.confirm("资产库文档", True),
            "storyboard": self.p.confirm("分镜脚本", True),
            "video_tasks": self.p.confirm("视频生成任务清单", True),
            "readme": self.p.confirm("项目README", True)
        }

        export_config = {
            "output_dir": project_dir,
            "project_name": project_name,
            "global_settings": global_settings,
            "cdp_data": cdp_data,
            "asset_config": asset_config,
            "storyboard_config": storyboard_config,
            "video_config": video_config,
            "export_items": export_items
        }

        # 确认导出
        if self.p.confirm(f"\n确认导出到 {project_dir}？"):
            self.p.print_success("导出配置已确认")
            return export_config
        else:
            return self.run(global_settings, cdp_data, asset_config,
                          storyboard_config, video_config)


# ============================================================================
# 主程序
# ============================================================================

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║         漫舟CDP Agent · 交互式漫剧文档生成器                ║
║                                                            ║
║         基于联易方舟六步流程 原封不动复刻                    ║
║                                                            ║
║         版本: v2.0.0 | 2026-03-27                         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

    p = InteractivePrompt()

    # 创建步骤实例
    step1 = Step1GlobalSettings(p)
    step2 = Step2StoryScript(p)
    step3 = Step3AssetLibrary(p)
    step4 = Step4Storyboard(p)
    step5 = Step5VideoGeneration(p)
    step6 = Step6Export(p)

    # 执行步骤1-6
    try:
        # 步骤1：全局设置
        global_settings = step1.run()

        # 步骤2：故事脚本
        cdp_data = step2.run(global_settings)

        # 步骤3：资产库
        asset_config = step3.run(cdp_data)

        # 步骤4：分镜脚本
        storyboard_config = step4.run(cdp_data, asset_config)

        # 步骤5：分镜视频
        video_config = step5.run(cdp_data)

        # 步骤6：导出配置
        export_config = step6.run(global_settings, cdp_data, asset_config,
                                 storyboard_config, video_config)

        # 完成
        p.print_header("🎉 项目配置完成！")

        print(f"""
  项目名称: {export_config['project_name']}
  输出目录: {export_config['output_dir']}

  下一步操作：
  1. 在 {export_config['output_dir']} 查看生成的文档
  2. 按照资产库生成角色图/场景图
  3. 在LibTV/可灵/Seedance中生成视频
  4. 使用剪映剪辑成片

  感谢使用漫舟CDP Agent！
        """)

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)


if __name__ == "__main__":
    main()
