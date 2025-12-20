# app/conversation/application/usecase/get_chat_message_usecase.py
from app.conversation.infrastructure.repository.chat_message_repository_impl import ChatMessageRepositoryImpl
from app.conversation.infrastructure.crypto.message_content_encryptor import MessageContentEncryptor, EncryptedPayload

class GetChatMessagesUseCase:
    def __init__(self, chat_message_repo: ChatMessageRepositoryImpl, crypto_service: MessageContentEncryptor):
        self.chat_message_repo = chat_message_repo
        self.crypto_service = crypto_service

    async def execute(self, room_id: str):
        messages = await self.chat_message_repo.find_by_room_id(room_id)
        decrypted = []

        for m in messages:
            # 1. IV나 암호화된 내용이 없는 경우를 대비한 처리
            if not m.iv or len(m.iv) != 16:
                # IV가 없으면 암호화되지 않은 일반 텍스트로 간주하거나 기본값 처리
                content = m.content_enc if m.content_enc else ""
                # 혹은 로그를 남겨 어떤 데이터가 문제인지 확인
                print(f"Warning: Invalid IV for message {m.id}. IV: {m.iv}")
            else:
                payload = EncryptedPayload(
                    ciphertext=m.content_enc,
                    iv=m.iv,
                    version=m.enc_version,
                )
                try:
                    content = self.crypto_service.decrypt(payload, iv=payload.iv)
                except Exception as e:
                    print(f"Decryption failed for message {m.id}: {e}")
                    content = "[Decryption Error]"

            decrypted.append({
                "id": m.id,
                "room_id": m.room_id,
                "account_id": m.account_id,
                "role": m.role,
                "content": content,
                "contents_type": m.contents_type,
                "created_at": m.created_at,
            })
        return decrypted