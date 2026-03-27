"""
断点恢复模块
管理 Agent 状态持久化，支持从断点恢复。
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import json
import os


class AgentState(Enum):
    INIT = "init"
    S0_PARSING = "s0_parsing"
    S0_DONE = "s0_done"
    S1_SETTINGS = "s1_settings"
    S1_DONE = "s1_done"
    S2_CDP = "s2_cdp"
    S2_DONE = "s2_done"
    S3_ASSETS = "s3_assets"
    S3_DONE = "s3_done"
    S4_SHOTS = "s4_shots"
    S4_DONE = "s4_done"
    S5_VIDEO = "s5_video"
    S5_DONE = "s5_done"
    COMPLETED = "completed"


@dataclass
class Checkpoint:
    state: AgentState
    project_name: str
    current_step: str
    completed_steps: list = field(default_factory=list)
    checkpoint_data: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "state": self.state.value,
            "project_name": self.project_name,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "checkpoint_data": self.checkpoint_data,
            "error": self.error,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Checkpoint":
        return cls(
            state=AgentState(data["state"]),
            project_name=data["project_name"],
            current_step=data["current_step"],
            completed_steps=data.get("completed_steps", []),
            checkpoint_data=data.get("checkpoint_data", {}),
            error=data.get("error"),
        )


class RecoveryManager:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.checkpoint_dir = os.path.join(project_path, ".manzhou")
        self.state_file = os.path.join(self.checkpoint_dir, "state.json")
        self.chain_ref_file = os.path.join(self.checkpoint_dir, "chain_ref.json")

    def save_checkpoint(self, checkpoint: Checkpoint):
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_json(), f, ensure_ascii=False, indent=2)

    def load_checkpoint(self) -> Optional[Checkpoint]:
        if not os.path.exists(self.state_file):
            return None
        with open(self.state_file, "r", encoding="utf-8") as f:
            return Checkpoint.from_json(json.load(f))

    def get_recovery_point(self) -> Optional[str]:
        """返回应该从哪个步骤恢复"""
        cp = self.load_checkpoint()
        if cp is None:
            return None
        if cp.state in [AgentState.S0_DONE, AgentState.S1_SETTINGS]:
            return "S1"
        elif cp.state in [AgentState.S1_DONE, AgentState.S2_CDP]:
            return "S2"
        elif cp.state in [AgentState.S2_DONE, AgentState.S3_ASSETS]:
            return "S3"
        elif cp.state in [AgentState.S3_DONE, AgentState.S4_SHOTS]:
            return "S4"
        elif cp.state in [AgentState.S4_DONE, AgentState.S5_VIDEO]:
            return "S5"
        elif cp.state == AgentState.S5_DONE:
            return "COMPLETED"
        return None


if __name__ == "__main__":
    # 测试断点恢复
    print("[Recovery] 测试断点恢复模块...")

    test_project = "/tmp/test_recovery_project"
    rm = RecoveryManager(test_project)

    # 测试保存检查点
    cp = Checkpoint(
        state=AgentState.S2_CDP,
        project_name="活着",
        current_step="s2_cdp",
        completed_steps=["S0", "S1"],
        checkpoint_data={"last_generated": "char_fugui"},
    )
    rm.save_checkpoint(cp)
    print(f"[Recovery] ✓ 检查点保存成功")

    # 测试恢复
    loaded = rm.load_checkpoint()
    print(f"[Recovery] ✓ 检查点加载成功: state={loaded.state.value}")

    # 测试恢复点计算
    recovery_point = rm.get_recovery_point()
    print(f"[Recovery] 恢复点: {recovery_point}")
