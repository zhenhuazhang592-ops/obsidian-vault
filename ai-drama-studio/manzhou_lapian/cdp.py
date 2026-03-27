"""漫舟拉片智能体 - CDP 资产库读取器"""
import json
import logging
from pathlib import Path
from typing import Optional
from .types import CDPData

logger = logging.getLogger(__name__)


class CDPReader:
    """读取漫舟资产库，生成 AI 可用的上下文"""

    def __init__(self, path: Optional[str] = None):
        self.path = path

    def read(self) -> CDPData:
        """读取 CDP JSON 文件，返回 CDPData 对象"""
        if not self.path or not Path(self.path).exists():
            logger.warning(f"CDP文件不存在或未指定: {self.path}")
            return CDPData()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)

            characters = data.get("characters", {})
            locations = data.get("locations", {})

            logger.info(f"CDP加载成功: {len(characters)}角色 / {len(locations)}场景")
            return CDPData(characters=characters, locations=locations)

        except json.JSONDecodeError as e:
            logger.error(f"CDP JSON 解析失败: {e}")
            return CDPData()
        except Exception as e:
            logger.error(f"CDP读取异常: {e}")
            return CDPData()
