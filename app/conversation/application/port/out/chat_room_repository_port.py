from abc import ABC, abstractmethod
from typing import Optional


class ChatRoomRepositoryPort(ABC):

    @abstractmethod
    async def create(
        self,
        room_id: str,
        account_id: int,
        title: Optional[str],
        category: str,
        division: str,
        out_api: str,
    ) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, room_id: str):
        pass

    @abstractmethod
    async def end_room(self, room_id: str) -> None:
        pass

    @abstractmethod
    async def find_by_account_id(self, account_id: int):
        pass