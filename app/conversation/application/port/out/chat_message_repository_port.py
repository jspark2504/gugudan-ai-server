from abc import ABC, abstractmethod


class ChatMessageRepositoryPort(ABC):

    @abstractmethod
    async def save_user_message(
        self,
        room_id: str,
        account_id: int,
        content_enc: bytes,
        iv: bytes,
        enc_version: int,
        contents_type: str,
    ) -> None:
        pass

    @abstractmethod
    async def save_assistant_message(
        self,
        room_id: str,
        content_enc: bytes,
        iv: bytes,
        enc_version: int,
        contents_type: str,
    ) -> None:
        pass

    @abstractmethod
    async def find_by_room_id(self, room_id: str):
        pass