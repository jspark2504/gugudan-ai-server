from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Numeric,
    DateTime,
    String,
    BigInteger,
    Enum as SAEnum,
)
from sqlalchemy.sql import func
from enum import Enum as PyEnum


class SatisfiedStatus(str, PyEnum):
    SATISFIED = "SATISFIED "
    UNSATISFIED = "UNSATISFIED"


from app.config.database.session import Base


class MessageFeedbackModel(Base):
    __tablename__ = "chat_message_feedback"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey("chat_message.id"))
    account_id = Column(Integer, ForeignKey("account.id"))
    satisfaction = Column(
        SAEnum(SatisfiedStatus, native_enum=True),
        nullable=False,
    )
    emotion_label = Column(String(50))
    emotion_score = Column(Numeric(5, 4))
    feedback_text = Column(String(1000))
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
