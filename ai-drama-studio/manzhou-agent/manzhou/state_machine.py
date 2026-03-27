"""状态机 - 12步执行流程 + Step依赖图 + 断点恢复"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime

from .constants import StepID, StepStatus, STEP_ORDER, HUMAN_GATE_STEPS, AUTO_STEPS


# =============================================================================
# Step状态记录
# =============================================================================

@dataclass
class StepState:
    step_id:    StepID
    status:     StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    input_ref:  str = ""    # 输入文件路径
    output_ref: str = ""    # 输出文件路径
    error_msg:  str = ""
    metadata:   dict = field(default_factory=dict)
    validation_report: dict = field(default_factory=dict)  # D1/D2/D3 评分结果

    def mark_running(self) -> None:
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now().isoformat()

    def mark_done(self, output_ref: str = "", metadata: dict = None) -> None:
        self.status = StepStatus.DONE
        self.completed_at = datetime.now().isoformat()
        self.output_ref = output_ref
        if metadata:
            self.metadata.update(metadata)

    def mark_failed(self, error: str) -> None:
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error_msg = error

    def mark_awaiting_human(self) -> None:
        self.status = StepStatus.AWAITING_HUMAN

    def is_blocked(self) -> bool:
        return self.status in (StepStatus.PENDING,)

    def has_passed_validation(self) -> bool:
        """Step 产出是否通过 Schema 校验"""
        return self.validation_report.get("is_passed", False)


# =============================================================================
# 项目会话状态
# =============================================================================

@dataclass
class ProjectSession:
    project_id:   str
    project_name: str
    episode:      str
    created_at:   str
    steps:        dict[StepID, StepState] = field(default_factory=dict)
    session_file: str = ""
    # --- Schema 契约携带 ---
    constraints:   dict = field(default_factory=dict)   # {step_id: constraints_dict}
    schema_version: str = "v10"  # 强制校验版本

    def __post_init__(self):
        if not self.steps:
            self.steps = {sid: StepState(step_id=sid) for sid in STEP_ORDER}

    def get_step_constraints(self, step_id: StepID) -> dict:
        """获取指定 Step 的输入约束（跨步传递的关键）"""
        return self.constraints.get(step_id.value, {})

    def set_step_constraints(self, step_id: StepID, constraints: dict) -> None:
        """设置指定 Step 的输出约束（供下一步使用）"""
        self.constraints[step_id.value] = constraints

    def to_dict(self) -> dict:
        return {
            "project_id":   self.project_id,
            "project_name": self.project_name,
            "episode":      self.episode,
            "created_at":   self.created_at,
            "schema_version": self.schema_version,
            "constraints":  self.constraints,
            "steps": {
                sid.value: {
                    "status":            s.status.value,
                    "started_at":        s.started_at,
                    "completed_at":      s.completed_at,
                    "input_ref":         s.input_ref,
                    "output_ref":        s.output_ref,
                    "error_msg":         s.error_msg,
                    "metadata":          s.metadata,
                    "validation_report": s.validation_report,
                }
                for sid, s in self.steps.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectSession":
        session = cls(
            project_id=data["project_id"],
            project_name=data["project_name"],
            episode=data["episode"],
            created_at=data["created_at"],
        )
        session.schema_version = data.get("schema_version", "v9")
        session.constraints = data.get("constraints", {})
        for sid, sdata in data.get("steps", {}).items():
            step_id = StepID(sid)
            session.steps[step_id] = StepState(
                step_id=step_id,
                status=StepStatus(sdata["status"]),
                started_at=sdata.get("started_at"),
                completed_at=sdata.get("completed_at"),
                input_ref=sdata.get("input_ref", ""),
                output_ref=sdata.get("output_ref", ""),
                error_msg=sdata.get("error_msg", ""),
                metadata=sdata.get("metadata", {}),
                validation_report=sdata.get("validation_report", {}),
            )
        return session

    def save(self, path: str) -> None:
        self.session_file = path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "ProjectSession":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


# =============================================================================
# 状态机引擎
# =============================================================================

class ManzhouStateMachine:
    """
    漫舟状态机引擎

    支持：
    - 完整流程执行
    - 断点恢复（从上次失败的Step继续）
    - Step依赖检查
    - 并行Step检测
    - 自动/人工Step分类
    """

    def __init__(self, session: Optional[ProjectSession] = None):
        self.session = session

    # ------------------------------------------------------------------ Step依赖

    def get_blocked_steps(self) -> list[StepID]:
        """获取当前被阻塞的Step（前置Step未完成）"""
        blocked = []
        for sid in STEP_ORDER:
            if self.session.steps[sid].status != StepStatus.PENDING:
                continue
            # 检查前置Step是否完成
            blockers = self._get_blockers(sid)
            if any(self.session.steps[b].status != StepStatus.DONE for b in blockers):
                blocked.append(sid)
        return blocked

    def _get_blockers(self, step_id: StepID) -> list[StepID]:
        """获取某Step的前置依赖"""
        # S5和S6都依赖S45
        if step_id in (StepID.S5, StepID.S6):
            return [StepID.S45]
        # S7依赖S45和S5
        if step_id == StepID.S7:
            return [StepID.S45, StepID.S5]

        # 线性依赖
        idx = STEP_ORDER.index(step_id)
        if idx == 0:
            return []
        return [STEP_ORDER[idx - 1]]

    # ------------------------------------------------------------------ 进度查询

    def get_progress(self) -> dict:
        """获取当前进度"""
        total = len(STEP_ORDER)
        done = sum(
            1 for s in self.session.steps.values()
            if s.status == StepStatus.DONE
        )
        running = sum(
            1 for s in self.session.steps.values()
            if s.status == StepStatus.RUNNING
        )
        failed = sum(
            1 for s in self.session.steps.values()
            if s.status == StepStatus.FAILED
        )
        awaiting = sum(
            1 for s in self.session.steps.values()
            if s.status == StepStatus.AWAITING_HUMAN
        )
        return {
            "total":   total,
            "done":    done,
            "running": running,
            "failed":  failed,
            "awaiting":awaiting,
            "pending": total - done - running - failed - awaiting,
            "pct":     round(done / total * 100, 1),
        }

    def get_next_runnable(self) -> list[StepID]:
        """获取下一步可执行的Step"""
        blocked = self.get_blocked_steps()
        pending = [
            sid for sid in STEP_ORDER
            if self.session.steps[sid].status == StepStatus.PENDING
            and sid not in blocked
        ]
        return pending

    def print_status(self) -> None:
        """打印状态机状态"""
        progress = self.get_progress()
        print(f"\n📊 状态机进度: {progress['done']}/{progress['total']} ({progress['pct']}%)")
        print("-" * 60)
        step_names = {
            StepID.S0: "Step 0  项目配置",
            StepID.S1: "Step 1  短剧改编",
            StepID.S2: "Step 2  IP解析",
            StepID.S3: "Step 3  剧本大纲",
            StepID.S45:"Step 4.5 导演控制塔",
            StepID.S5: "Step 5  资产设计",
            StepID.S6: "Step 6  分镜图",
            StepID.S7: "Step 7  分镜脚本 ✅",
        }
        icons = {
            StepStatus.DONE:           "✅",
            StepStatus.RUNNING:        "🔄",
            StepStatus.FAILED:         "❌",
            StepStatus.SKIPPED:        "⏭",
            StepStatus.AWAITING_HUMAN: "⏸",
            StepStatus.PENDING:        "⬜",
        }
        for sid in STEP_ORDER:
            s = self.session.steps[sid]
            icon = icons.get(s.status, "⬜")
            name = step_names.get(sid, sid.value)
            meta = ""
            if s.error_msg:
                meta = f" ← {s.error_msg[:30]}"
            elif s.output_ref:
                meta = f" ← {os.path.basename(s.output_ref)}"
            print(f"  {icon} {name}  {meta}")
        print("-" * 60)

    # ------------------------------------------------------------------ 执行控制

    def start_step(self, step_id: StepID) -> None:
        """标记Step开始"""
        self.session.steps[step_id].mark_running()
        print(f"\n{'=' * 60}")
        print(f"🚀 {step_id.value.upper()} 开始执行")
        print("=" * 60)

    def complete_step(
        self,
        step_id: StepID,
        output_ref: str = "",
        metadata: dict = None,
    ) -> None:
        """标记Step完成"""
        self.session.steps[step_id].mark_done(output_ref, metadata)
        print(f"✅ {step_id.value.upper()} 完成 → {output_ref or 'OK'}")

    def fail_step(self, step_id: StepID, error: str) -> None:
        """标记Step失败"""
        self.session.steps[step_id].mark_failed(error)
        print(f"❌ {step_id.value.upper()} 失败: {error}")

    def is_human_gate(self, step_id: StepID) -> bool:
        return step_id in HUMAN_GATE_STEPS

    def is_auto_step(self, step_id: StepID) -> bool:
        return step_id in AUTO_STEPS

    # ------------------------------------------------------------------ 断点恢复

    def find_resume_point(self) -> Optional[StepID]:
        """
        找到断点恢复起点：
        1. 找到第一个 FAILED 状态 → 从该Step重试
        2. 找到第一个 RUNNING 状态 → 从该Step继续
        3. 找到第一个 AWAITING_HUMAN → 从该Step继续
        4. 全部DONE → 返回None（全部完成）
        """
        for sid in STEP_ORDER:
            status = self.session.steps[sid].status
            if status in (StepStatus.FAILED, StepStatus.RUNNING, StepStatus.AWAITING_HUMAN):
                return sid
        return None

    def resume(self) -> list[StepID]:
        """
        从断点恢复，返回需要重跑的Step列表
        """
        resume_point = self.find_resume_point()
        if resume_point is None:
            print("✅ 所有Step已完成，无需恢复")
            return []

        # 从断点开始的所有未完成Step
        resume_idx = STEP_ORDER.index(resume_point)
        to_resume = [
            sid for sid in STEP_ORDER[resume_idx:]
            if self.session.steps[sid].status != StepStatus.DONE
        ]
        print(f"🔄 断点恢复：从 {resume_point.value} 开始 ({len(to_resume)}个Step)")
        return to_resume

    # ------------------------------------------------------------------ Schema 校验

    def validate_step_input(self, step_id: StepID, input_data: dict) -> tuple[bool, str]:
        """
        在 Step 执行前，校验输入数据是否符合 Schema 约束

        返回：(is_valid, error_msg)
        """
        constraints = self.session.get_step_constraints(step_id)
        if not constraints:
            # 无约束 → 跳过校验（可能是 Step 0）
            return True, ""

        # 检查必需字段
        required_fields = constraints.get("required_fields", [])
        missing = [f for f in required_fields if f not in input_data or not input_data[f]]
        if missing:
            return False, f"缺少必需字段: {missing}"

        return True, ""

    def record_step_output(
        self,
        step_id: StepID,
        output_ref: str,
        validation_report: dict,
        next_constraints: dict = None,
    ) -> None:
        """
        记录 Step 输出 + 校验结果 + 为下一步注入约束

        这是跨步 Schema 传递的核心方法
        """
        self.session.steps[step_id].mark_done(output_ref)
        self.session.steps[step_id].validation_report = validation_report

        # 为下一步设置输入约束
        if next_constraints:
            step_idx = STEP_ORDER.index(step_id)
            if step_idx + 1 < len(STEP_ORDER):
                next_step = STEP_ORDER[step_idx + 1]
                self.session.set_step_constraints(next_step, next_constraints)
                print(f"  📋 为 {next_step.value} 注入约束: {list(next_constraints.keys())}")
