"""
状态机模块
漫剧创作状态机 (S0-S5)
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from .chain_ref import ChainRef
from .recovery import AgentState, Checkpoint, RecoveryManager
from .schema import STYLE_GUIDE_SCHEMA, CHARACTER_DNA_SCHEMA, SCENE_DNA_SCHEMA, ITEM_DNA_SCHEMA


class DramStateMachine:
    """
    漫剧创作状态机 (S0-S5)

    S0: 解析小说 → 输出解析报告
    S1: 全局设置 → 输出风格指南 (规范锚点)
    S2: CDP资产包 → 输出角色/场景/道具DNA
    S3: 资产库 → 输出图像生成提示词
    S4: 分镜脚本 → 输出每镜脚本+运镜规范
    S5: 视频生成 → 输出Kling+Seedance双版本提示词
    """

    STATES = [
        "init", "s0_parsing", "s0_done",
        "s1_settings", "s1_done",
        "s2_cdp", "s2_done",
        "s3_assets", "s3_done",
        "s4_shots", "s4_done",
        "s5_video", "s5_done",
        "completed"
    ]

    def __init__(self, project_path: str, project_name: str):
        self.project_path = project_path
        self.project_name = project_name
        self.recovery = RecoveryManager(project_path)
        self.chain_ref = ChainRef(project_path=project_path)
        self.state = "init"
        self._load_or_init()

    def _load_or_init(self):
        cp = self.recovery.load_checkpoint()
        if cp:
            self.state = cp.state.value
            # 恢复 chain_ref
            loaded_ref = ChainRef.load(self.recovery.chain_ref_file)
            if loaded_ref:
                self.chain_ref = loaded_ref

    def advance(self, step_output: dict) -> str:
        """推进状态机，step_output 包含当前步骤的输出摘要"""
        transitions = {
            "init": ("s0_parsing", "s0_done"),
            "s0_parsing": ("s0_done", "s1_settings"),
            "s0_done": ("s1_settings", "s1_done"),
            "s1_settings": ("s1_done", "s2_cdp"),
            "s1_done": ("s2_cdp", "s2_done"),
            "s2_cdp": ("s2_done", "s3_assets"),
            "s2_done": ("s3_assets", "s3_done"),
            "s3_assets": ("s3_done", "s4_shots"),
            "s3_done": ("s4_shots", "s4_done"),
            "s4_shots": ("s4_done", "s5_video"),
            "s5_video": ("s5_done", "completed"),
        }

        current = self.state
        if current in transitions:
            next_state = transitions[current][1]
            self.state = next_state
            self._save_state(step_output)
            return next_state
        return current

    def _save_state(self, step_output: dict):
        """保存状态和链式引用"""
        completed = self._get_completed_steps()
        cp = Checkpoint(
            state=AgentState(self.state),
            project_name=self.project_name,
            current_step=self.state,
            completed_steps=completed,
            checkpoint_data=step_output,
        )
        self.recovery.save_checkpoint(cp)
        self.chain_ref.save(self.recovery.chain_ref_file)

    def _get_completed_steps(self) -> list:
        done_states = ["s0_done", "s1_done", "s2_done", "s3_done", "s4_done", "s5_done", "completed"]
        return [s for s in self.STATES if s <= self.state and s in done_states]

    def get_next_action(self) -> str:
        """返回下一个应执行的动作"""
        action_map = {
            "init": "S0_PARSE_NOVEL",
            "s0_done": "S1_GLOBAL_SETTINGS",
            "s1_done": "S2_BUILD_CDP",
            "s2_done": "S3_GENERATE_ASSETS",
            "s3_done": "S4_WRITE_SHOT_SCRIPTS",
            "s4_done": "S5_GENERATE_VIDEO_PROMPTS",
            "completed": "ALL_DONE",
        }
        return action_map.get(self.state, "UNKNOWN")

    def can_proceed(self) -> bool:
        """检查是否可以继续"""
        return self.state != "completed"

    def status(self) -> dict:
        return {
            "state": self.state,
            "next_action": self.get_next_action(),
            "can_proceed": self.can_proceed(),
            "chain_ref_steps": list(self.chain_ref.refs.keys()),
        }


if __name__ == "__main__":
    # 测试状态机
    print("[StateMachine] 测试状态机...")

    sm = DramStateMachine(project_path="/tmp/test_state_machine", project_name="活着")

    print(f"[StateMachine] 初始状态: {sm.state}")
    print(f"[StateMachine] 下一步动作: {sm.get_next_action()}")

    # 模拟 S0 完成
    sm.advance({"step": "S0", "anchors": {}})
    print(f"[StateMachine] S0 完成，当前状态: {sm.state}")

    # 模拟 S1 完成
    sm.advance({"step": "S1", "anchors": {"style": "v1.0.0"}})
    print(f"[StateMachine] S1 完成，当前状态: {sm.state}")

    # 状态检查
    print(f"[StateMachine] 完整状态: {sm.status()}")
