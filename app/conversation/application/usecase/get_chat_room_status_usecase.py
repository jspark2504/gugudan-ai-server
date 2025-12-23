from app.conversation.application.port.out.chat_room_repository_port import ChatRoomRepositoryPort


class GetChatRoomStatusUseCase:
    def __init__(self, repo: ChatRoomRepositoryPort):
        self.repo = repo

    async def execute(self, room_id: str, account_id: int) -> str:
        return await self.repo.find_status_by_room_id(room_id, account_id)
