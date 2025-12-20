from datetime import datetime, timedelta
from typing import List

from sqlalchemy import literal
from sqlalchemy.orm import Session, aliased

from app.config.database.session import get_db_session
from app.conversation.infrastructure.orm.chat_message_feedback_orm import MessageFeedbackModel
from app.conversation.infrastructure.orm.chat_message_orm import ChatMessageOrm
from app.ml.application.port.ml_repository_port import MLRepositoryPort
from app.ml.domain.output_message import CounselRow


class MLRepositoryImpl(MLRepositoryPort):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, 'db'):
            self.db: Session = get_db_session()

    def get_counsel_data(self, start: str, end: str) -> List[CounselRow]:
        try:
            m1 = aliased(ChatMessageOrm)  # USER
            m2 = aliased(ChatMessageOrm)  # ASSISTANT

            start_dt = datetime.strptime(start, "%Y%m%d")
            end_dt = datetime.strptime(end, "%Y%m%d") + timedelta(days=1)

            user_q = (
                self.db.query(
                    literal("USER").label("role"),
                    m1.content_enc.label("message"),
                    literal(None).label("parent"),
                    m1.created_at.label("created_at")
                )
                .join(m2, m1.room_id == m2.room_id)
                .join(MessageFeedbackModel, m2.id == MessageFeedbackModel.message_id)
                .filter(
                    m1.role == "USER",
                    m2.role == "ASSISTANT",
                    m2.parent_message_id == m1.id,
                    MessageFeedbackModel.satisfaction == "SATISFIED",
                    m1.created_at >= start_dt,
                    m1.created_at < end_dt,
                )
            )

            assistant_q = (
                self.db.query(
                    literal("ASSISTANT").label("role"),
                    m2.content_enc.label("message"),
                    m2.parent_message_id.label("parent"),
                    m2.created_at.label("created_at")
                )
                .join(m1, m1.room_id == m2.room_id)
                .join(MessageFeedbackModel, m2.id == MessageFeedbackModel.message_id)
                .filter(
                    m1.role == "USER",
                    m2.role == "ASSISTANT",
                    m2.parent_message_id == m1.id,
                    MessageFeedbackModel.satisfaction == "SATISFIED",
                    m2.created_at >= start_dt,
                    m2.created_at < end_dt,
                )
            )

            rows = user_q.union_all(assistant_q).all()

            result: List[CounselRow] = [
                {
                    "role": row.role,
                    "message": row.message,
                    "parent": row.parent,
                    "created_at": row.created_at
                }
                for row in rows
            ]

            print(f"result : {result}")

            return result

        finally:
            self.db.close()


