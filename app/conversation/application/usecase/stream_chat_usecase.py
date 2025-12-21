from typing import AsyncIterator
from fastapi import HTTPException


class StreamChatUsecase:
    def __init__(
            self,
            chat_room_repo,
            chat_message_repo,
            llm_chat_port,
            usage_meter,
            crypto_service,
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

        await self.usage_meter.check_available(account_id)

        # 1. 데이터 로드 및 애그리거트 생성
        room_orm = await self.chat_room_repo.find_by_id(room_id)
        msg_orms = await self.chat_message_repo.find_by_room_id(room_id)

        from app.conversation.domain.conversation.aggregate import Conversation
        conversation = Conversation(room=room_orm, messages=msg_orms)

        if not conversation.is_active():
            raise HTTPException(status_code=400, detail="채팅방이 활성 상태가 아닙니다.")

        # 2. 유저 메시지 저장 (부모: 기존 마지막 메시지)
        user_encrypted, user_iv = self.crypto_service.encrypt(message)
        saved_user = await self.chat_message_repo.save_message(
            room_id=room_id,
            account_id=account_id,
            role="USER",
            content_enc=user_encrypted,
            iv=user_iv,
            parent_id=conversation.get_last_id(),  # 족보 연결
            enc_version=self.crypto_service.get_version(),
            contents_type=contents_type,
        )

        # 3. 프롬프트 구성 (말씀하신 페르소나 적용)
        # 시스템 지침: 상담사의 성격과 제약 사항 정의
        system_instruction = (
            "당신은 연애, 커플, 이혼 등 관계에서 발생하는 감정과 대화 문제를 함께 나누는 따뜻한 대화 동반자입니다. "
            "사용자를 진단하거나 분석하려 하지 마세요. 사용자가 스스로 생각을 정리할 수 있도록 경청하고 공감하며 대화를 이어가세요.\n\n"
        )

        # 히스토리 컨텍스트: 애그리거트에서 복호화된 대화 이력을 가져옴
        history_context = conversation.get_prompt_context(self.crypto_service)

        # 최종 프롬프트 조립
        full_prompt = (
            f"{system_instruction}"
            f"{history_context}"
            f"사용자: {message}\n"
            f"상담사: "
        )

        # 4. AI 응답 스트리밍
        assistant_full_message = ""
        async for chunk in self.llm_chat_port.call_gpt(full_prompt):
            assistant_full_message += chunk
            yield chunk.encode("utf-8")

        # 5. AI 메시지 저장 (부모: 유저 메시지 ID)
        assistant_encrypted, assistant_iv = self.crypto_service.encrypt(assistant_full_message)

        await self.chat_message_repo.save_message(
            room_id=room_id,
            account_id=account_id,
            role="ASSISTANT",
            content_enc=assistant_encrypted,
            iv=assistant_iv,
            parent_id=saved_user.id,  # 👈 유저 메시지를 부모로 지정
            enc_version=self.crypto_service.get_version(),
            contents_type=contents_type,
        )

        # 6. 세션 확정 및 기록
        self.chat_message_repo.db.commit()
        await self.usage_meter.record_usage(account_id, len(message), len(assistant_full_message))
