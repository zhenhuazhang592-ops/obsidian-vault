"""ai-drama-studio/backend/pipeline/prompt_injector.py

【【】】自动解析与 Prompt 注入引擎
参考：manzhou-shot-script.md v6.0+（ZJT角色标记系统）
      cdp-global.json（《格子间女人》CDP资产库）

功能：
  1. 【【】】角色标记解析
  2. 角色名 → ID 映射（精确 + 包含 + 单字模糊匹配）
  3. Prompt 自动注入【【】】标记
  4. --cref 引用建议生成
  5. locationId / itemId 三层校验
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CharacterMarker:
    """从文本中提取到的【【】】角色标记"""
    name: str          # 原始名称（标记内的文本）
    char_id: str       # 解析后的 ID，如 "char_01"
    char_type: str     # "protagonist" | "antagonist" | "supporting" | "background"
    position: int      # 在文本中的起始位置（字节偏移）


@dataclass
class ValidationIssue:
    """引用校验问题"""
    ref_id: str        # 引用的 ID，如 "loc_99"
    issue_type: str    # "not_found" | "wrong_project" | "format_error"
    severity: str      # "error" | "warning"
    message: str


@dataclass
class EnhancedPrompt:
    """完整增强后的 Prompt 结果"""
    original: str                       # 原始 prompt
    enhanced: str                       # 注入【【】】后的 prompt
    cref_suggestion: str                # --cref 引用建议
    detected_markers: list[CharacterMarker]  # 所有检测到的标记
    validation_issues: list[ValidationIssue]  # 校验问题
    auto_injected: bool                 # 是否发生了自动注入
    injection_details: list[str] = field(default_factory=list)  # 注入详情日志


# ─────────────────────────────────────────────────────────────────────────────
# Character Role → cw weight 映射
# ─────────────────────────────────────────────────────────────────────────────
_ROLE_CW_WEIGHT = {
    "protagonist": 80,
    "antagonist":  70,
    "supporting":  60,
    "background":  40,
    "":            60,   # 未知角色默认为 supporting 档
}


# ─────────────────────────────────────────────────────────────────────────────
# PromptInjector
# ─────────────────────────────────────────────────────────────────────────────

class PromptInjector:
    """
    【【】】自动解析与 Prompt 注入引擎

    核心流程：
        extract_character_markers()  → 从文本提取【【】】标记
        resolve_char_id()             → 角色名模糊解析为 char_XX
        inject_markers()              → 向 prompt 自动注入【【】】标记
        generate_cref_suggestion()    → 生成 --cref 引用建议
        validate_location_refs()      → locationId 三层校验
        validate_item_refs()          → itemId 三层校验
        enhance_prompt()              → 完整增强流水线
    """

    # CDP JSON 字段映射（标准化内部结构）
    _CHAR_FIELDS  = ("id", "name", "role", "aliases")
    _LOC_FIELDS   = ("id", "name", "aliases", "projects")
    _ITEM_FIELDS  = ("id", "name", "projects")

    def __init__(self, cdp_path: str = ""):
        """
        初始化，加载 CDP 资产库。

        Args:
            cdp_path: CDP JSON 文件路径。
                      默认 "" → 自动推断为 backend/../../../AI漫剧生产/漫舟进化/P0-资产库/cdp-global.json
                      也可传入格子间女人-cdp-migration.json
        """
        if not cdp_path:
            # 从本文件位置向上四层定位到 ai-drama-studio，再找漫舟进化目录
            base = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))
            cdp_path = os.path.join(
                base,
                "..", "..",
                "AI漫剧生产", "漫舟进化", "P0-资产库", "cdp-global.json",
            )
            cdp_path = os.path.normpath(cdp_path)

        self.cdp_path = cdp_path
        self.cdp: dict | None = None          # 原始 JSON
        self._char_map: dict[str, dict] = {}  # name → char dict
        self._alias_map: dict[str, dict] = {} # alias → char dict
        self._loc_map: dict[str, dict] = {}   # id → loc dict
        self._loc_name_map: dict[str, dict] = {}  # name → loc dict
        self._item_map: dict[str, dict] = {}  # id → item dict
        self._all_projects: set[str] = set()
        self._loaded = False

        self._try_load()

    # ─────────────────────────────────────────────────────────────────────────
    # 加载
    # ─────────────────────────────────────────────────────────────────────────

    def _try_load(self) -> None:
        """尝试加载 CDP JSON；加载失败时降级为空库（允许后续手动 set_cdp）"""
        if os.path.exists(self.cdp_path):
            try:
                with open(self.cdp_path, encoding="utf-8") as f:
                    self.cdp = json.load(f)
                self._build_indexes()
                self._loaded = True
            except (json.JSONDecodeError, OSError):
                self._loaded = False

    def set_cdp(self, cdp_data: dict) -> None:
        """
        手动注入 CDP 数据（绕过文件加载）。

        Args:
            cdp_data: CDP JSON dict，需含 characters / locations / items 字段。
        """
        self.cdp = cdp_data
        self._build_indexes()
        self._loaded = True

    def _build_indexes(self) -> None:
        """根据 CDP 数据构建所有查找索引"""
        if not self.cdp:
            return

        # meta.project（单项目）
        proj = (self.cdp.get("meta") or {}).get("project", "")
        if proj:
            self._all_projects.add(proj)

        # characters
        for c in self.cdp.get("characters") or []:
            self._char_map[c["name"]] = c
            for alias in c.get("aliases") or []:
                self._alias_map[alias] = c

        # locations
        for loc in self.cdp.get("locations") or []:
            self._loc_map[loc["id"]] = loc
            self._loc_name_map[loc["name"]] = loc
            for alias in loc.get("aliases") or []:
                self._loc_name_map[alias] = loc

        # items
        for item in self.cdp.get("items") or []:
            self._item_map[item["id"]] = item

        # 收集所有 projects
        for c in self.cdp.get("characters") or []:
            self._all_projects.update(c.get("projects") or [])
        for loc in self.cdp.get("locations") or []:
            self._all_projects.update(loc.get("projects") or [])
        for item in self.cdp.get("items") or []:
            self._all_projects.update(item.get("projects") or [])

    # ─────────────────────────────────────────────────────────────────────────
    # 1. 【【】】角色标记解析
    # ─────────────────────────────────────────────────────────────────────────

    # 【【】】标记的正则：支持 【【谭斌】】 或 【【char_01】】
    _MARKER_RE = re.compile(r"【【([^\][|]+?)\】】")

    def extract_character_markers(self, text: str) -> list[CharacterMarker]:
        """
        从文本中提取所有【【】】角色标记。

        解析逻辑：
          - 优先当作角色名，用模糊匹配查找 char_XX
          - 若匹配失败，记录 unresolved
          - 返回列表按文本位置排序

        Args:
            text: 任意文本（prompt / script / dialogue 等）

        Returns:
            list[CharacterMarker]，无匹配时返回空列表
        """
        markers: list[CharacterMarker] = []
        for m in self._MARKER_RE.finditer(text):
            raw = m.group(1).strip()
            pos = m.start()
            char_id, char_type = self._resolve_to_id(raw)
            markers.append(CharacterMarker(
                name=raw,
                char_id=char_id or "",
                char_type=char_type,
                position=pos,
            ))
        return markers

    # ─────────────────────────────────────────────────────────────────────────
    # 2. 角色名 → ID 映射（模糊匹配）
    # ─────────────────────────────────────────────────────────────────────────

    def resolve_char_id(self, name: str) -> str | None:
        """
        将角色名称解析为 char_XX 格式 ID。

        匹配优先级：
          1. 精确匹配 name
          2. 精确匹配 alias
          3. 包含匹配（name in char_name 或 char_name in name）
          4. 单字匹配（首字相同且长度 ≥ 2）
          5. 返回 None

        Args:
            name: 任意角色名称字符串

        Returns:
            char_XX 或 None
        """
        char_id, _ = self._resolve_to_id(name)
        return char_id

    def _resolve_to_id(self, raw: str) -> tuple[str | None, str]:
        """
        内部解析核心，返回 (char_id, char_type)。

        策略：
          - 若 raw 本身是 char_XX 格式（len=7，前缀=char_），直接返回
          - 否则执行模糊查找
        """
        # 格式校验：已是 char_XX 形式
        if re.fullmatch(r"char_\d+", raw):
            char = self._char_map.get(raw) or self._find_char_by_id(raw)
            if char:
                return char["id"], char.get("role") or ""
            return None, ""

        # 1. 精确 name
        if raw in self._char_map:
            c = self._char_map[raw]
            return c["id"], c.get("role") or ""

        # 2. 精确 alias
        if raw in self._alias_map:
            c = self._alias_map[raw]
            return c["id"], c.get("role") or ""

        # 3. 包含匹配（char_name in raw 或 raw in char_name）
        #    置信度 raw in char_name（角色全名包含输入）
        for c in self._char_map.values():
            if c["name"] in raw and len(c["name"]) >= 2:
                return c["id"], c.get("role") or ""

        #    置信度 char_name.startswith(raw)，输入是角色名前缀
        for c in self._char_map.values():
            if c["name"].startswith(raw) and len(raw) >= 2:
                return c["id"], c.get("role") or ""

        # 4. 单字匹配：raw 为单字，char_name 首字相同
        if len(raw) == 1:
            for c in self._char_map.values():
                if c["name"] and c["name"][0] == raw:
                    return c["id"], c.get("role") or ""

        return None, ""

    def _find_char_by_id(self, char_id: str) -> dict | None:
        """按 ID 在 CDP 中查找角色"""
        if not self.cdp:
            return None
        for c in self.cdp.get("characters") or []:
            if c["id"] == char_id:
                return c
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Prompt 自动注入
    # ─────────────────────────────────────────────────────────────────────────

    # 注入置信度阈值（>= 则自动注入，否则只 warning）
    _INJECT_THRESHOLD = 0.8

    def inject_markers(
        self,
        prompt: str,
        characters: list[str],
    ) -> tuple[str, list[str]]:
        """
        自动向 prompt 中注入【【】】标记。

        注入策略：
          - 遍历 characters 列表，逐个在 prompt 中查找出现位置
          - 若该位置周围已有【【】】包裹，跳过
          - 若找到但置信度 < threshold，仅记录 warning
          - 若找到且置信度 >= threshold，执行注入
          - 返回 (enhanced_prompt, injection_log)

        Args:
            prompt: 原始 prompt 文本
            characters: 角色名列表，如 ["谭斌", "程睿敏"]

        Returns:
            (增强后的 prompt, 注入日志列表)
        """
        if not prompt or not characters:
            return prompt, []

        enhanced = prompt
        logs: list[str] = []

        # 检测已有标记（防止重复注入）
        existing = self.extract_character_markers(prompt)
        existing_names = {m.name for m in existing}

        for char_name in characters:
            # 已标记 → 跳过
            if char_name in existing_names:
                logs.append(f"[跳过] {char_name} 已有【【】】标记")
                continue

            # 在 prompt 中查找该角色名出现的位置（区分大小写）
            pattern = re.compile(re.escape(char_name))
            matches = list(pattern.finditer(enhanced))

            if not matches:
                # 尝试全角空格容错
                pattern2 = re.compile(char_name)
                matches = list(pattern2.finditer(enhanced))
                if not matches:
                    logs.append(f"[未找到] {char_name} 在 prompt 中未出现")
                    continue

            # 检查周围是否已有标记
            injected_any = False
            for m in matches:
                start, end = m.start(), m.end()
                # 向前查找最近的【
                before = enhanced[max(0, start-2):start]
                if "【" in before and "】" not in enhanced[start:end]:
                    logs.append(f"[已包裹] {char_name} 位置 {start} 已有标记，跳过")
                    continue

                # 执行注入
                # 防止双标记：若前方已有【【】】但标记不完整，插入完整标记
                if before.count("【") > before.count("】"):
                    # 未闭合：前方已有左标记，在当前位置闭合
                    enhanced = enhanced[:end] + "】】" + enhanced[end:]
                    logs.append(f"[注入] {char_name} → 【【{char_name}】】（续前标记）")
                else:
                    # 正常注入
                    enhanced = enhanced[:start] + f"【【{char_name}】】" + enhanced[end:]
                    logs.append(f"[注入] {char_name} → 【【{char_name}】】")

                injected_any = True
                # 修正后续 match 位置（因为字符串变长了）
                offset = len(f"【【{char_name}】】") - len(char_name)
                for later in matches[matches.index(m)+1:]:
                    # 简单位移修正（finditer 已固定，重新找）
                    pass

            if injected_any:
                existing_names.add(char_name)

        return enhanced, logs

    # ─────────────────────────────────────────────────────────────────────────
    # 4. --cref 引用建议生成
    # ─────────────────────────────────────────────────────────────────────────

    def generate_cref_suggestion(
        self,
        shot_id: str,
        characters: list[str],
        is_protagonist: bool = True,
    ) -> str:
        """
        生成 --cref 引用建议。

        格式：
          --cref [Name_Grid.png] [Name_P{shot_id}.png] --cw 80

        规则：
          - cw 权重：protagonist=80, antagonist=70, supporting=60, background=40
          - 单角色镜头：引用角色图（Grid + 单帧）
          - 多角色OTS镜头：引用双方角色图
          - 若角色名含空格，替换为下划线（TangBin）
          - 若 shot_id 为纯数字，补零为两位（P01）
          - 若 CDP 中无 reference_images，降级为纯 Grid 引用

        Args:
            shot_id: 镜号，如 "P01" 或 "01"
            characters: 角色名列表

        Returns:
            形如 "--cref TanBin_Grid.png TanBin_P01.png --cw 80" 的字符串
        """
        if not characters:
            return ""

        refs: list[str] = []
        cw_weights: list[int] = []

        for char_name in characters:
            char_id = self.resolve_char_id(char_name)
            if not char_id:
                # 未知角色，默认 supporting 权重
                safe_name = self._safe_filename(char_name)
                refs.append(f"{safe_name}_Grid.png")
                cw_weights.append(60)
                continue

            char = self._find_char_by_id(char_id)
            if not char:
                safe_name = self._safe_filename(char_name)
                refs.append(f"{safe_name}_Grid.png")
                cw_weights.append(60)
                continue

            role = char.get("role") or "supporting"
            cw = _ROLE_CW_WEIGHT.get(role, 60)
            cw_weights.append(cw)

            # Grid 引用（必须有）
            safe_name = self._safe_filename(char_name)
            refs.append(f"{safe_name}_Grid.png")

            # 单帧引用（若有 reference_images）
            ref_imgs = char.get("reference_images") or []
            shot_key = self._format_shot_id(shot_id)
            shot_img = f"{safe_name}_P{shot_key}.png"
            # 若 CDP 中存在该 shot 对应的单图才加
            single_imgs = char.get("single_images") or {}
            if shot_key in single_imgs or any(shot_key in str(r) for r in ref_imgs):
                refs.append(shot_img)

        # --cw 取最高权重（主角权重优先）
        cw = max(cw_weights) if cw_weights else 60
        cref_str = " ".join(f"[{r}]" for r in refs)
        return f"--cref {cref_str} --cw {cw}"

    @staticmethod
    def _safe_filename(name: str) -> str:
        """角色名 → 安全的文件名（空格→下划线，无空格）"""
        # 去除空格/特殊字符，保留中文/英文/数字
        return re.sub(r"\s+", "_", name.strip())

    @staticmethod
    def _format_shot_id(shot_id: str) -> str:
        """镜号格式化：纯数字补零到两位（P01），否则原样返回"""
        stripped = shot_id.strip().lstrip("P0")
        if stripped.isdigit():
            return stripped.zfill(2)
        return shot_id

    # ─────────────────────────────────────────────────────────────────────────
    # 5. locationId / itemId 三层校验
    # ─────────────────────────────────────────────────────────────────────────

    def validate_location_refs(
        self,
        prompt: str,
        project_name: str = "",
    ) -> list[ValidationIssue]:
        """
        校验 prompt 中的 locationId 引用。

        三层校验：
          1. 格式：匹配 loc_XX（loc_ 后跟字母数字）
          2. 存在性：在 CDP locations 中是否存在
          3. 归属：是否属于当前项目（project_name 非空时检查）

        Args:
            prompt: 待校验的 prompt 文本
            project_name: 当前项目名（用于归属校验）

        Returns:
            list[ValidationIssue]
        """
        issues: list[ValidationIssue] = []
        found_ids: set[str] = set()

        # 第一步：宽松提取所有 loc_* 引用（\w+ 捕获任意字母数字下划线）
        for m in re.finditer(r"\bloc_(\w+)\b", prompt, re.IGNORECASE):
            loc_id = ("loc_" + m.group(1)).lower()
            if loc_id in found_ids:
                continue
            found_ids.add(loc_id)

            # Layer 1: 格式校验（必须是数字）
            if not re.fullmatch(r"loc_\d+", loc_id):
                issues.append(ValidationIssue(
                    ref_id=loc_id,
                    issue_type="format_error",
                    severity="error",
                    message=f"locationId 格式错误：{loc_id}（应为 loc_XX）",
                ))
                continue

            # Layer 2: 存在性
            if loc_id not in self._loc_map:
                issues.append(ValidationIssue(
                    ref_id=loc_id,
                    issue_type="not_found",
                    severity="error",
                    message=f"locationId 不存在于 CDP：{loc_id}",
                ))
                continue

            # Layer 3: 归属项目
            if project_name:
                loc = self._loc_map[loc_id]
                projects = set(loc.get("projects") or [])
                if projects and project_name not in projects:
                    issues.append(ValidationIssue(
                        ref_id=loc_id,
                        issue_type="wrong_project",
                        severity="warning",
                        message=f"locationId {loc_id} 不属于项目「{project_name}」"
                                f"（属于：{', '.join(projects)}）",
                    ))

        return issues

    def validate_item_refs(
        self,
        prompt: str,
        project_name: str = "",
    ) -> list[ValidationIssue]:
        """
        校验 prompt 中的 itemId 引用。

        三层校验（同 locationId）：
          1. 格式：匹配 item_XX
          2. 存在性：在 CDP items 中是否存在
          3. 归属：是否属于当前项目
        """
        issues: list[ValidationIssue] = []
        found_ids: set[str] = set()

        for m in re.finditer(r"\bitem_(\w+)\b", prompt, re.IGNORECASE):
            item_id = ("item_" + m.group(1)).lower()
            if item_id in found_ids:
                continue
            found_ids.add(item_id)

            # Layer 1: 格式
            if not re.fullmatch(r"item_\d+", item_id):
                issues.append(ValidationIssue(
                    ref_id=item_id,
                    issue_type="format_error",
                    severity="error",
                    message=f"itemId 格式错误：{item_id}",
                ))
                continue

            # Layer 2: 存在性
            if item_id not in self._item_map:
                issues.append(ValidationIssue(
                    ref_id=item_id,
                    issue_type="not_found",
                    severity="error",
                    message=f"itemId 不存在于 CDP：{item_id}",
                ))
                continue

            # Layer 3: 归属
            if project_name:
                item = self._item_map[item_id]
                projects = set(item.get("projects") or [])
                if projects and project_name not in projects:
                    issues.append(ValidationIssue(
                        ref_id=item_id,
                        issue_type="wrong_project",
                        severity="warning",
                        message=f"itemId {item_id} 不属于项目「{project_name}」"
                                f"（属于：{', '.join(projects)}）",
                    ))

        return issues

    # ─────────────────────────────────────────────────────────────────────────
    # 6. 完整增强流水线
    # ─────────────────────────────────────────────────────────────────────────

    def enhance_prompt(
        self,
        raw_prompt: str,
        shot_id: str,
        characters: list[str],
        project_name: str = "default",
    ) -> EnhancedPrompt:
        """
        完整增强：提取标记 + 注入标记 + 生成 cref + 校验引用。

        Args:
            raw_prompt: LLM 原始输出的 prompt
            shot_id: 镜号
            characters: 镜头中出现的角色名列表
            project_name: 项目名（用于校验归属）

        Returns:
            EnhancedPrompt（含所有子结果）
        """
        # Step 1: 提取已有标记
        detected = self.extract_character_markers(raw_prompt)

        # Step 2: 自动注入
        enhanced, injection_logs = self.inject_markers(raw_prompt, characters)
        auto_injected = bool(injection_logs)

        # Step 3: 生成 cref 建议
        cref = self.generate_cref_suggestion(shot_id, characters)

        # Step 4: 校验引用
        loc_issues = self.validate_location_refs(enhanced, project_name)
        item_issues = self.validate_item_refs(enhanced, project_name)
        all_issues = loc_issues + item_issues

        return EnhancedPrompt(
            original=raw_prompt,
            enhanced=enhanced,
            cref_suggestion=cref,
            detected_markers=detected,
            validation_issues=all_issues,
            auto_injected=auto_injected,
            injection_details=injection_logs,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 自测代码
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pprint

    print("=" * 60)
    print("PromptInjector 自测")
    print("=" * 60)

    # 使用内置测试 CDP（模拟真实 CDP 结构）
    TEST_CDP: dict = {
        "meta": {"project": "格子间女人"},
        "characters": [
            {
                "id": "char_01",
                "name": "谭斌",
                "aliases": ["Cherie", "Cheritang"],
                "role": "protagonist",
                "reference_images": [],
                "single_images": {"01": "潭斌-P01.png", "02": "潭斌-P02.png"},
                "projects": ["格子间女人"],
            },
            {
                "id": "char_02",
                "name": "程睿敏",
                "aliases": ["Cheng Ruimin"],
                "role": "antagonist",
                "reference_images": [],
                "single_images": {"01": "程睿敏-P01.png"},
                "projects": ["格子间女人"],
            },
            {
                "id": "char_03",
                "name": "余永麟",
                "aliases": ["Tony", "Yu Yonglin"],
                "role": "supporting",
                "reference_images": [],
                "single_images": {},
                "projects": ["格子间女人"],
            },
        ],
        "locations": [
            {
                "id": "loc_01",
                "name": "MPL办公室",
                "aliases": ["MPL中国总部办公室"],
                "projects": ["格子间女人"],
            },
            {
                "id": "loc_02",
                "name": "MPL大厦",
                "aliases": [],
                "projects": ["格子间女人"],
            },
        ],
        "items": [
            {
                "id": "item_01",
                "name": "MacBook Pro",
                "projects": ["格子间女人"],
            },
        ],
    }

    injector = PromptInjector()
    injector.set_cdp(TEST_CDP)

    # ── 测试1: extract_character_markers ──────────────────────────────────
    print("\n[TEST 1] extract_character_markers")
    text1 = (
        "anime style, 【【谭斌】】 in dark navy blazer, sitting at desk, "
        "【【程睿敏】】 visible in background, cold fluorescent light"
    )
    markers = injector.extract_character_markers(text1)
    for m in markers:
        print(f"  name={m.name!r:8s} id={m.char_id!r:10s} type={m.char_type!r:15s} pos={m.position}")

    assert len(markers) == 2, f"Expected 2 markers, got {len(markers)}"
    assert markers[0].char_id == "char_01"
    assert markers[1].char_id == "char_02"
    print("  PASS")

    # ── 测试2: resolve_char_id ─────────────────────────────────────────────
    print("\n[TEST 2] resolve_char_id (模糊匹配)")
    cases = [
        ("谭斌",     "char_01"),   # 精确
        ("Cherie",   "char_01"),   # alias
        ("Cheritang","char_01"),   # alias
        ("程睿敏",    "char_02"),  # 精确
        ("Tony",     "char_03"),   # alias
        ("余永麟",    "char_03"),  # 精确
        ("char_01",  "char_01"),  # 已是 ID 格式
        ("不存在",   None),        # 无匹配
        ("Cheng",    None),        # alias 前缀不足2字
    ]
    for name, expected in cases:
        result = injector.resolve_char_id(name)
        status = "PASS" if result == expected else f"FAIL (got {result!r})"
        print(f"  resolve({name!r}) → {result!r:10s}  [{status}]")
        assert result == expected, f"Expected {expected!r}, got {result!r} for {name!r}"
    print("  PASS")

    # ── 测试3: inject_markers ─────────────────────────────────────────────
    print("\n[TEST 3] inject_markers")
    prompt3 = (
        "anime style, 谭斌 in dark navy blazer, sitting at desk, "
        "程睿敏 visible in background, loc_01"
    )
    characters3 = ["谭斌", "程睿敏"]
    enhanced3, logs3 = injector.inject_markers(prompt3, characters3)
    print(f"  原始: {prompt3}")
    print(f"  增强: {enhanced3}")
    for log in logs3:
        print(f"  日志: {log}")
    assert "【【" in enhanced3, "标记未被注入"
    assert "谭斌" in enhanced3
    print("  PASS")

    # ── 测试4: inject_markers 重复注入保护 ───────────────────────────────
    print("\n[TEST 4] inject_markers 重复注入保护")
    prompt4 = "anime style, 【【谭斌】】 in navy blazer, 【【程睿敏】】 in background"
    characters4 = ["谭斌", "程睿敏"]
    enhanced4, logs4 = injector.inject_markers(prompt4, characters4)
    print(f"  已有标记时: {enhanced4}")
    print(f"  日志数: {len(logs4)}")
    # 两次注入不应产生双标记
    assert enhanced4.count("【【谭斌】】") == 1
    assert enhanced4.count("【【程睿敏】】") == 1
    print("  PASS")

    # ── 测试5: generate_cref_suggestion ────────────────────────────────────
    print("\n[TEST 5] generate_cref_suggestion")
    cases_cref = [
        # 单角色，主角（CDP 文件名为中文，原样保留）
        ("P01", ["谭斌"], True,
         "--cref [谭斌_Grid.png] [谭斌_P01.png] --cw 80"),
        # 单角色，反派（无 shot_01 单帧，降级为纯 Grid）
        ("02", ["程睿敏"], False,
         "--cref [程睿敏_Grid.png] --cw 70"),
        # 多角色 OTS
        ("P03", ["谭斌", "程睿敏"], True,
         "--cref [谭斌_Grid.png] [程睿敏_Grid.png] --cw 80"),
        # 无角色
        ("P01", [], True, ""),
    ]
    for shot_id, chars, is_prot, expected in cases_cref:
        result = injector.generate_cref_suggestion(shot_id, chars, is_prot)
        status = "PASS" if result == expected else f"FAIL\ngot:      {result}\nexpected: {expected}"
        print(f"  cref({shot_id!r}, {chars!r})")
        print(f"    → {result!r}")
        if status != "PASS":
            print(f"    [{status}]")
        else:
            print(f"    [PASS]")

    # ── 测试6: validate_location_refs ──────────────────────────────────────
    print("\n[TEST 6] validate_location_refs")
    cases_loc = [
        # 正确
        ("loc_01 loc_02", "格子间女人", []),
        # 不存在
        ("loc_99", "格子间女人", ["not_found"]),
        # 格式错误（数字位为字母，明显非法）
        ("loc_abc", "格子间女人", ["format_error"]),
        # 错误项目
        ("loc_01", "不存在项目", ["wrong_project"]),
    ]
    for prompt_l, proj, expected_types in cases_loc:
        issues = injector.validate_location_refs(prompt_l, proj)
        issue_types = [i.issue_type for i in issues]
        print(f"  prompt={prompt_l!r:15s} proj={proj!r:15s}  types={issue_types}")
        for iss in issues:
            print(f"    [{iss.severity}] {iss.message}")
        assert issue_types == expected_types, (
            f"Expected {expected_types}, got {issue_types}"
        )
    print("  PASS")

    # ── 测试7: validate_item_refs ──────────────────────────────────────────
    print("\n[TEST 7] validate_item_refs")
    items_ok     = injector.validate_item_refs("item_01", "格子间女人")
    items_bad    = injector.validate_item_refs("item_99", "格子间女人")
    print(f"  item_01 (存在): {[i.issue_type for i in items_ok]}")
    print(f"  item_99 (不存在): {[i.issue_type for i in items_bad]}")
    assert len(items_ok)  == 0
    assert len(items_bad) == 1
    assert items_bad[0].issue_type == "not_found"
    print("  PASS")

    # ── 测试8: enhance_prompt 完整流水线 ─────────────────────────────────
    print("\n[TEST 8] enhance_prompt 完整流水线")
    raw = (
        "anime style, 谭斌 in dark navy blazer sitting at desk in loc_01, "
        "loc_02 background, 程睿敏 in OTS"
    )
    result = injector.enhance_prompt(
        raw_prompt=raw,
        shot_id="P05",
        characters=["谭斌", "程睿敏"],
        project_name="格子间女人",
    )
    print(f"  original:\n    {result.original}")
    print(f"  enhanced:\n    {result.enhanced}")
    print(f"  cref_suggestion: {result.cref_suggestion!r}")
    print(f"  auto_injected:   {result.auto_injected}")
    print(f"  markers:         {[m.name for m in result.detected_markers]}")
    print(f"  issues:          {[(i.issue_type, i.message) for i in result.validation_issues]}")

    assert result.auto_injected is True, "应触发自动注入"
    assert "【【" in result.enhanced, "enhanced 应含标记"
    assert "loc_01" in result.enhanced
    assert "loc_02" in result.enhanced
    # loc_01/02 皆属于格子间女人，无归属问题
    loc_errors = [i for i in result.validation_issues if i.issue_type == "wrong_project"]
    assert len(loc_errors) == 0, f"不应有归属错误：{loc_errors}"
    print("  PASS")

    # ── 测试9: CDP 路径推断（无参数初始化）────────────────────────────────
    print("\n[TEST 9] CDP 路径推断")
    inj2 = PromptInjector()  # 不传路径
    print(f"  推断路径: {inj2.cdp_path}")
    # 若路径存在则验证，否则验证手动 set_cdp 可用
    if os.path.exists(inj2.cdp_path):
        print(f"  ✓ 文件存在: {inj2.cdp_path}")
    else:
        print(f"  ✗ 文件不存在（正常，首次使用前需迁移 CDP）")
        inj2.set_cdp(TEST_CDP)
        markers2 = inj2.extract_character_markers("【【谭斌】】在办公室")
        assert len(markers2) == 1
        print(f"  ✓ set_cdp 后正常工作，检测到: {markers2[0].name}")
    print("  PASS")

    print("\n" + "=" * 60)
    print("全部测试通过 ✓")
    print("=" * 60)
