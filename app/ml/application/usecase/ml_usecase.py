import base64
import os

from dotenv import load_dotenv

from app.common.infrastructure.encryption import AESEncryption
from app.config.anonymizer import Anonymizer
from app.ml.application.port.ml_repository_port import MLRepositoryPort

load_dotenv()
AES_KEY = base64.b64decode(os.getenv("AES_KEY"))

class MLUseCase:

    def __init__(self, ml_repository: MLRepositoryPort):
        self.ml_repository = ml_repository
        pass

    def make_data_to_jsonl(self, start: str, end: str) -> dict:

        ## 사용자 상담 데이터 가져오기 (Feedback SATISFIED Data)
        chat_datas = self.ml_repository.get_counsel_data(start, end)

        anonymizer = Anonymizer()

        messages = [
            {"role": "system", "content": "당신은 연애 심리 상담가입니다."}
        ]

        for row in chat_datas:
            # 1. 복호화
            decrypted = AESEncryption.decrypt(
                encrypted_data_base64=row.message,
                iv_base64=row.iv,
                key=AES_KEY
            )

            # 2. 비식별화
            content = anonymizer.anonymize(decrypted)

            # 3. role 매핑
            if row.role == "USER":
                messages.append({"role": "user", "content": content})
            elif row.role == "ASSISTANT":
                messages.append({"role": "assistant", "content": content})

        print(f"messages: {messages}")

        return {"messages": messages}

    def get_counsel_data(self, chat_message_id: int, chat_message_feedback_id: int) -> dict:
        pass
