from abc import ABC, abstractmethod


class UsageMeterPort(ABC):

    @abstractmethod
    async def check_available(
        self,
        account_id: int,
    ) -> None:
        """쿼터 초과 시 Exception"""
        pass

    @abstractmethod
    async def record_usage(
        self,
        account_id: int,
        input_tokens: int,
        token_count: int,
    ) -> None:
        pass
