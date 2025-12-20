import os
from typing import AsyncIterator
from openai import AsyncOpenAI
from app.conversation.application.port.out.llm_chat_port import LlmChatPort
from dotenv import load_dotenv

load_dotenv()


class OpenAiAdapter(LlmChatPort):
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
    async def stream_chat(self, messages: list) -> AsyncIterator[str]:
        """
        OpenAI API를 통해 스트리밍 응답을 생성합니다.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True  # 스트리밍 활성화
            )

            async for chunk in response:
                # content가 있는 경우에만 추출하여 yield
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            # 에러 발생 시 로그를 남기거나 적절한 에러 메시지 반환
            print(f"OpenAI API Error: {e}")
            yield "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."