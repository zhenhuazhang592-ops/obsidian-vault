#!/usr/bin/env python3
"""资产师 Agent —— 提取+管理角色/道具/场景"""
import json, sys, pathlib, sqlite3
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class AssetAgent(BaseAgent):
    name = "asset"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        self.db_path = pathlib.Path(__file__).parent.parent / "db" / "jike.db"

        # 文本 adapter
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.text_adapter = AdapterRegistry.get(adapter_name, model_cfg)

        # 图像 adapter
        img_adapter_name = self.cfg.get("image_adapter", "seedream")
        img_model_cfg = self.cfg["models"].get(img_adapter_name, {})
        self.image_adapter = AdapterRegistry.get(img_adapter_name, img_model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "extract":
            return self._extract_assets(params.get("outline", {}))
        if action == "generate_image":
            return self._generate_asset_image(params.get("asset_id"))
        if action == "list":
            return self._list_assets(params.get("project_id"))
        if action == "save":
            return self._save_asset(params.get("asset"))
        return {"error": f"Unknown action: {action}"}

    def _extract_assets(self, outline: dict) -> list[dict]:
        system_prompt = get_prompt("asset-role")
        user_prompt = (
            f"请根据以下大纲，提取所有角色信息（JSON数组）：\n\n"
            + json.dumps(outline, ensure_ascii=False)
        )

        result = self.text_adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={"type": "array"},
        )

        return result if isinstance(result, list) else []

    def _generate_asset_image(self, asset_id: int) -> dict:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT name, prompt, type FROM t_asset WHERE id = ?", (asset_id,)
        ).fetchone()
        conn.close()

        if not row:
            return {"error": f"Asset {asset_id} not found"}

        name, prompt, asset_type = row
        result = self.image_adapter.invoke(
            prompt=prompt or name,
            aspect_ratio="1:1" if asset_type == "role" else "16:9",
        )
        return result

    def _list_assets(self, project_id: int) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id, name, type, state FROM t_asset WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "name": r[1], "type": r[2], "state": r[3]}
            for r in rows
        ]

    def _save_asset(self, asset: dict) -> dict:
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            """INSERT INTO t_asset
               (project_id, name, intro, type, prompt, state)
               VALUES (?, ?, ?, ?, ?, 'draft')""",
            (
                asset.get("project_id"),
                asset.get("name"),
                asset.get("intro"),
                asset.get("type"),
                asset.get("prompt"),
            ),
        )
        conn.commit()
        asset_id = cur.lastrowid
        conn.close()
        return {"id": asset_id, **asset}


if __name__ == "__main__":
    AssetAgent().run()
