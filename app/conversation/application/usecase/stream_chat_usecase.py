import os  # IV 생성을 위해 필요
from typing import AsyncIterator

from app.conversation.application.port.out.chat_message_repository_port import ChatMessageRepositoryPort
from app.conversation.application.port.out.chat_room_repository_port import ChatRoomRepositoryPort
from app.conversation.application.port.out.llm_chat_port import LlmChatPort
from app.conversation.application.port.out.usage_meter_port import UsageMeterPort
# 암호화 서비스를 가져옵니다 (경로는 프로젝트 구조에 맞게 조정하세요)
from app.conversation.infrastructure.crypto.message_content_encryptor import MessageContentEncryptor

class StreamChatUsecase:
    def __init__(
        self,
        chat_room_repo: ChatRoomRepositoryPort,
        chat_message_repo: ChatMessageRepositoryPort,
        llm_chat_port: LlmChatPort,
        usage_meter: UsageMeterPort,
        crypto_service: MessageContentEncryptor, # 1. 암호화 서비스 주입
    ):
        self.chat_room_repo = chat_room_repo
        self.chat_message_repo = chat_message_repo
        self.llm_chat_port = llm_chat_port
        self.usage_meter = usage_meter
        self.crypto_service = crypto_service

    async def execute(
        self,
        room_id: str,
        account_id: int,
        message: str,
        contents_type: str,
    ) -> AsyncIterator[bytes]:

        # 1️⃣ 사용 가능 여부 체크
        await self.usage_meter.check_available(account_id)

        # 2️⃣ USER 메시지 암호화 및 저장
        # 16바이트 랜덤 IV 생성
        user_iv = os.urandom(16) 
        # 실제 암호화 수행
        user_encrypted = self.crypto_service.encrypt(message, iv=user_iv)

        await self.chat_message_repo.save_user_message(
            room_id=room_id,
            account_id=account_id,
            content_enc=user_encrypted, # 암호화된 데이터
            iv=user_iv,                 # 생성된 16바이트 IV
            enc_version=1,
            contents_type=contents_type,
        )

        # 3️⃣ LLM 요청
        messages = [{"role": "user", "content": message}]
        assistant_full_message = ""

        async for chunk in self.llm_chat_port.stream_chat(messages):
            assistant_full_message += chunk
            yield chunk.encode("utf-8")

        # 4️⃣ ASSISTANT 메시지 암호화 및 저장
        # 어시스턴트용 별도의 16바이트 랜덤 IV 생성
        assistant_iv = os.urandom(16)
        assistant_encrypted = self.crypto_service.encrypt(assistant_full_message, iv=assistant_iv)

        await self.chat_message_repo.save_assistant_message(
            room_id=room_id,
            account_id=account_id,
            content_enc=assistant_encrypted, # 암호화된 데이터
            iv=assistant_iv,                 # 생성된 16바이트 IV
            enc_version=1,
            contents_type=contents_type,
        )

        # 5️⃣ 사용량 기록
        await self.usage_meter.record_usage(
            account_id,
            len(message),
            len(assistant_full_message),
        )