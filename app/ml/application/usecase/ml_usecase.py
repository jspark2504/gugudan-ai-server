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

        # USER 메시지 맵
        user_map = {}

        for row in chat_datas:
            if row["role"] != "USER":
                continue

            decrypted = AESEncryption.decrypt(
                encrypted_data_base64=row["message"],
                iv_base64=row["iv"],
                key=AES_KEY
            )

            user_map[row["id"]] = anonymizer.anonymize(decrypted)

        jsonl_data = []

        for row in chat_datas:
            if row["role"] != "ASSISTANT":
                continue

            user_content = user_map.get(row["parent"])
            if not user_content:
                continue

            decrypted = AESEncryption.decrypt(
                encrypted_data_base64=row["message"],
                iv_base64=row["iv"],
                key=AES_KEY
            )

            assistant_content = anonymizer.anonymize(decrypted)

            jsonl_data.append({
                "messages": [
                    {"role": "system", "content": "당신은 연애 심리 상담가입니다."},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]
            })

        return {"messages": jsonl_data}
