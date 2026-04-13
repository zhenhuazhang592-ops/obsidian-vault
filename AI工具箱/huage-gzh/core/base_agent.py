# BaseAgent - Agent基类
# 所有Agent的父类，提供标准化接口

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass
import time

from core.message_hub import MessageHub, Message, MessageType


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    output: Any = None
    error: str = ""
    duration: float = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration": self.duration
        }


class BaseAgent(ABC):
    """Agent基类"""

    name: str = "base"
    description: str = ""

    def __init__(self, hub: MessageHub = None):
        self.hub = hub or MessageHub()
        self._start_time: float = 0

    @abstractmethod
    def execute(self, input_data: Any) -> AgentResult:
        """执行Agent逻辑，子类必须实现"""
        pass

    def run(self, input_data: Any) -> AgentResult:
        """标准运行流程：计时 -> 执行 -> 发布消息 -> 返回"""
        self._start_time = time.time()

        # 发布开始状态
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "started", "agent": self.name}
        ))

        try:
            result = self.execute(input_data)
            result.duration = time.time() - self._start_time

            if result.success:
                self.hub.publish(Message(
                    type=self._get_output_type(),
                    agent=self.name,
                    content=result.output
                ))
            else:
                self.hub.publish(Message(
                    type=MessageType.ERROR,
                    agent=self.name,
                    content=result.error
                ))

            return result

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"{self.name}执行异常: {str(e)}",
                duration=time.time() - self._start_time
            )

    def _get_output_type(self) -> MessageType:
        """子类返回对应的输出消息类型"""
        return MessageType.STATUS
