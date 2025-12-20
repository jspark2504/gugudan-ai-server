from app.ml.application.port.ml_repository_port import MLRepositoryPort
from sqlalchemy.orm import Session
from typing import Optional

from app.ml.infrastructure.orm.chat_message_analysis_model import ChatMessageAnalysisModel
from app.config.database.session import get_db_session
from app.message_log.infrastructure.orm.message_log_models import ChatRoomModel
from app.message_log.infrastructure.orm.message_log_models import ChatMessageModel

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

    def get_counsel_data(self, chat_message_id: int, chat_message_feedback_id: int) -> dict:
        try:
            data = self.db.query(ChatMessageModel).filter(ChatMessageModel.id == chat_message_id,
                                                           ChatMessageModel.id == chat_message_id).first()
        finally:
            return None

    def make_counsel_data_to_analysis(self, message_id: int, feedback_id: int) -> Optional[ChatMessageAnalysisModel]:
        """
        상담 내역을 chat_message_analysis 테이블에 맞춰 저장한다.

        :param message_id: 채팅 내역 id
        :param feedback_id: 피드백 id
        :return:
        """

