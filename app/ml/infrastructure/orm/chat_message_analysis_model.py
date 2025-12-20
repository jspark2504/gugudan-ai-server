from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    ForeignKey,
    Numeric,
    DateTime,
    String,
    BigInteger,
    Enum as SAEnum,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func

from app.config.database.session import Base


class AnalysisType(str, PyEnum):
    SENTIMENT = "감정"
    EMOTION = "감성"
    SUMMARY = "요약"


class AnalysisStatus(str, PyEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ChatMessageAnalysisModel(Base):
    __tablename__ = "chat_message_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey("chat_message.id"), nullable=False)
    room_id = Column(String(36), ForeignKey("chat_room.id"), nullable=False)

    provider = Column(String(30))
    model = Column(String(50))
    model_version = Column(String(30))

    analysis_type = Column(
        SAEnum(AnalysisType, native_enum=True),
        nullable=False
    )

    emotion_label = Column(String(50))
    emotion_score = Column(Numeric(5, 4))

    result_json = Column(JSON)

    status = Column(
        SAEnum(AnalysisStatus, native_enum=True),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
