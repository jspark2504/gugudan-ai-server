from Crypto.Cipher import AES
from dataclasses import dataclass

from Crypto.Random import get_random_bytes


@dataclass
class EncryptedPayload:
    ciphertext: bytes
    iv: bytes
    version: int = 1  # 기본값 설정


class MessageContentEncryptor:
    def __init__(self, secret_key: bytes, iv: bytes | None = None):
        # AES-256을 위해 key는 32바이트여야 합니다. 
        # base64 디코딩 후 32바이트인지 확인하는 로직이 있으면 좋습니다.
        self.secret_key = secret_key
        self.default_iv = iv

    def encrypt(self, plain_text: str, iv: bytes | None = None) -> bytes:
        """암호화 후 ciphertext(bytes)만 반환 (Usecase 로직에 맞춤)"""
        # 넘겨받은 iv가 없으면 새로 생성
        target_iv = iv if iv else get_random_bytes(16)

        cipher = AES.new(self.secret_key, AES.MODE_CFB, iv=target_iv)
        return cipher.encrypt(plain_text.encode("utf-8"))

    def decrypt(self, payload: EncryptedPayload, iv: bytes | None = None) -> str:
        """복호화 수행"""
        # payload.iv 또는 직접 전달받은 iv 사용
        target_iv = iv if iv else payload.iv

        if not target_iv or len(target_iv) != 16:
            raise ValueError(f"IV length must be 16 bytes. Got: {len(target_iv) if target_iv else 'None'}")

        cipher = AES.new(self.secret_key, AES.MODE_CFB, iv=target_iv)
        decrypted = cipher.decrypt(payload.ciphertext)
        return decrypted.decode("utf-8")