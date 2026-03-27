"""
链式引用追踪器
确保每步输出正确引用上游 ID，规范链式数据流。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StepRef:
    step: str          # S0/S1/S2/S3/S4/S5
    file: str          # 输出文件路径
    anchors: dict      # 关键 ID 映射 {角色ID: 角色名, 场景ID: 场景名, ...}


@dataclass
class ChainRef:
    """引用追踪器"""
    project_path: str
    refs: dict = field(default_factory=dict)  # {step: StepRef}

    def register(self, step: str, anchors: dict, file: str):
        """注册某步的输出锚点"""
        self.refs[step] = StepRef(step=step, file=file, anchors=anchors)

    def get_ref(self, step: str) -> Optional[StepRef]:
        return self.refs.get(step)

    def check_shot_refs(self, shot_entry: dict) -> tuple[bool, list]:
        """
        检查某镜脚本是否正确引用了上游 ID
        返回: (is_valid, violation_list)
        """
        violations = []
        required_refs = {
            "location_id": "S2",
            "character_ids": "S2",
            "item_ids": "S2",
        }
        for field, upstream_step in required_refs.items():
            if upstream_step in self.refs:
                upstream_anchors = self.refs[upstream_step].anchors
                value = shot_entry.get(field)
                if value:
                    # 检查 value 是否在 upstream_anchors 中
                    if isinstance(value, list):
                        for v in value:
                            if v not in upstream_anchors:
                                violations.append(f"{field}: {v} not in {upstream_step} anchors")
                    elif value not in upstream_anchors:
                        violations.append(f"{field}: {value} not in {upstream_step} anchors")
        return (len(violations) == 0, violations)

    def save(self, path: str):
        """保存到 JSON 文件"""
        import json
        data = {
            step: {"file": r.file, "anchors": r.anchors}
            for step, r in self.refs.items()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> Optional["ChainRef"]:
        """从 JSON 文件恢复"""
        import json
        import os
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ref = cls(project_path=os.path.dirname(path))
        for step, rdata in data.items():
            ref.refs[step] = StepRef(
                step=step,
                file=rdata["file"],
                anchors=rdata["anchors"]
            )
        return ref


if __name__ == "__main__":
    # 测试链式引用追踪器
    print("[ChainRef] 测试链式引用追踪器...")

    chain = ChainRef(project_path="/tmp/test_project")

    # 注册 S2 锚点
    chain.register(
        step="S2",
        anchors={
            "char_fugui": "福贵",
            "char_jiazhen": "家珍",
            "scene_maowu": "茅屋",
            "scene_tianjian": "田间",
        },
        file="01-CDP资产包/CDP-JSON.md"
    )

    # 测试检查引用
    shot = {
        "location_id": "scene_maowu",
        "character_ids": ["char_fugui", "char_jiazhen"],
        "item_ids": ["item_yuanbao"],
    }

    is_valid, violations = chain.check_shot_refs(shot)
    print(f"[ChainRef] 引用检查: {'✓ 通过' if is_valid else '✗ 失败'}")
    if violations:
        for v in violations:
            print(f"  - {v}")

    # 测试保存和加载
    test_path = "/tmp/test_chain_ref.json"
    chain.save(test_path)
    loaded = ChainRef.load(test_path)
    print(f"[ChainRef] 持久化: ✓ 保存/加载成功")
    print(f"[ChainRef] 已注册步骤: {list(chain.refs.keys())}")
