import hashlib
import re

from dotenv import load_dotenv

load_dotenv()

class Anonymizer:
    def __init__(self):
        self.cache = {}

    @staticmethod
    def decrypt(value: str, type_of_value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
        return f"__{type_of_value}_{digest}__"

    def anonymize(self, text: str) -> str:
        if not text:
            return text

        # 이메일
        text = re.sub(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            lambda m: self.decrypt(m.group(), "email"),
            text,
        )

        # 전화번호 (010-xxxx-xxxx, 010xxxxxxxx, 02-xxx-xxxx 등)
        text = re.sub(
            r"(01[016789]|02|0[3-9][0-9])[- ]?\d{3,4}[- ]?\d{4}",
            lambda m: self.decrypt(m.group(), "number"),
            text,
        )

        # 한국 주소 (시/도 + 구/군 + 동/로)
        text = re.sub(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n,]{3,30}",
            lambda m: self.decrypt(m.group(), "address"),
            text,
        )

        return text
