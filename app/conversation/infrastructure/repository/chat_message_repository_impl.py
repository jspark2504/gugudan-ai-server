from app.conversation.application.port.out.chat_message_repository_port import ChatMessageRepositoryPort
from app.conversation.infrastructure.orm.chat_message_orm import ChatMessageOrm
from app.config.database.session import get_db_session
from sqlalchemy.orm import Session
from Crypto.Random import get_random_bytes

class ChatMessageRepositoryImpl(ChatMessageRepositoryPort):

    def __init__(self, session: Session | None = None):
        self.db: Session = session or get_db_session()

    async def save_user_message(self, content_enc: bytes, iv: bytes | None = None, **kwargs):
        # IV가 없으면 16바이트 랜덤 생성
        if not iv:
            iv = get_random_bytes(16)
        msg = ChatMessageOrm(
            role="USER",
            content_enc=content_enc,
            iv=iv,
            **kwargs
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    async def save_assistant_message(self, content_enc: bytes, iv: bytes | None = None, **kwargs):
        if not iv:
            iv = get_random_bytes(16)
        msg = ChatMessageOrm(
            role="ASSISTANT",
            content_enc=content_enc,
            iv=iv,
            **kwargs
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    async def find_by_room_id(self, room_id: str):
        return (
            self.db.query(ChatMessageOrm)
            .filter(ChatMessageOrm.room_id == room_id)
            .order_by(ChatMessageOrm.created_at.asc())
            .all()
        )
