from abc import ABC, abstractmethod
from typing import AsyncIterator


class LlmChatPort(ABC):

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """
        messages:
        [
          {"role": "system|user|assistant", "content": "..."}
        ]
        """
        pass
