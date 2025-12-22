import base64
import hashlib
import json
import logging
import os

from dotenv import load_dotenv

from app.common.infrastructure.encryption import AESEncryption
from app.config.anonymizer import Anonymizer
from app.ml.application.port.ml_repository_port import MLRepositoryPort
from app.ml.application.port.vector_db_port import VectorDBPort
from app.ml.infrastructure.vector_db.embedding_service import EmbeddingService

load_dotenv()
AES_KEY = base64.b64decode(os.getenv("AES_KEY"))

logger = logging.getLogger(__name__)


class MLUseCase:

    def __init__(
        self,
        ml_repository: MLRepositoryPort,
        vector_db: VectorDBPort = None
    ):
        self.ml_repository = ml_repository
        self.vector_db = vector_db

    def make_data_to_jsonl(self, start: str, end: str) -> dict:

        ## 사용자 상담 데이터 가져오기 (Feedback SATISFIED Data)
        chat_datas = self.ml_repository.get_counsel_data(start, end)

        ## 유저 정보 가져오기
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

        # 벡터 DB에 저장 (유사도 80% 이하일 경우에만)
        if self.vector_db:
            self._save_to_vector_db(jsonl_data)

        return {"messages": jsonl_data}

    def _save_to_vector_db(self, jsonl_data: list):
        """벡터 DB에 데이터 저장 (유사도 80% 이하일 경우에만).

        Args:
            jsonl_data: JSONL 형식의 메시지 데이터 리스트
        """
        if not self.vector_db:
            logger.warning("Vector DB is not initialized, skipping vector storage")
            return

        try:
            vectors_to_save = []
            saved_count = 0
            skipped_count = 0

            for data_item in jsonl_data:
                # 메시지 내용을 텍스트로 변환 (유사도 검사용)
                messages = data_item.get("messages", [])
                user_content = ""
                assistant_content = ""

                for msg in messages:
                    if msg.get("role") == "user":
                        user_content = msg.get("content", "")
                    elif msg.get("role") == "assistant":
                        assistant_content = msg.get("content", "")

                # user와 assistant 내용을 결합하여 검색용 텍스트 생성
                search_text = f"{user_content} {assistant_content}".strip()

                if not search_text:
                    continue

                # 벡터 임베딩 생성
                embedding = EmbeddingService.generate_embedding(search_text)

                # 유사도 검사 (80% 이상이면 스킵)
                similar_results = self.vector_db.search_similar(
                    query_vector=embedding,
                    limit=1,
                    score_threshold=0.8  # 80% 이상 유사도
                )

                if similar_results:
                    # 유사도가 80% 이상인 데이터가 존재함
                    max_score = similar_results[0].get("score", 0.0)
                    logger.debug(
                        f"Skipping duplicate data (similarity: {max_score:.2%})"
                    )
                    skipped_count += 1
                    continue

                # 유사도가 80% 이하이므로 저장
                # 고유 ID 생성 (메시지 내용의 해시값 사용)
                content_hash = hashlib.md5(
                    json.dumps(data_item, sort_keys=True).encode()
                ).hexdigest()
                vector_id = int(content_hash[:15], 16)  # 해시를 정수로 변환

                vectors_to_save.append({
                    "id": vector_id,
                    "vector": embedding,
                    "payload": {
                        "messages": data_item.get("messages", []),
                        "user_content": user_content,
                        "assistant_content": assistant_content,
                    }
                })
                saved_count += 1

            # 벡터 DB에 일괄 저장
            if vectors_to_save:
                success = self.vector_db.upsert_vectors(vectors_to_save)
                if success:
                    logger.info(
                        f"Vector DB: Saved {saved_count} vectors, "
                        f"Skipped {skipped_count} duplicates"
                    )
                else:
                    logger.error("Failed to save vectors to Qdrant")
            else:
                logger.info(
                    f"Vector DB: All {skipped_count} items were duplicates, "
                    "nothing to save"
                )

        except Exception as e:
            logger.error(f"Error saving to vector DB: {e}", exc_info=True)
