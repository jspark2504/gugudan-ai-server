import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class AESEncryption:


    def __init__(self):

        key_b64 = os.getenv("AES_KEY")
        iv_b64 = os.getenv("AES_IV")

        if not key_b64 or not iv_b64:
            raise ValueError(
                "AES_KEY and AES_IV environment variables are required. "
                "Please set them in .env file."
            )

        try:
            self.key = base64.b64decode(key_b64)
            self.iv = base64.b64decode(iv_b64)
        except Exception as e:
            raise ValueError(f"Failed to decode AES_KEY or AES_IV: {e}")

        if len(self.key) != 32:
            raise ValueError(
                f"Failed to initialize encryption: Key must be 32 bytes for AES-256 "
                f"(got {len(self.key)} bytes). Please check your AES_KEY in .env"
            )
        if len(self.iv) != 16:
            raise ValueError(
                f"Failed to initialize encryption: IV must be 16 bytes "
                f"(got {len(self.iv)} bytes). Please check your AES_IV in .env"
            )

        self.version = 1

    def encrypt(self, plaintext: str) -> tuple[bytes, bytes]:
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(self.iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        return encrypted_data, self.iv

    def decrypt(self, ciphertext: bytes, iv: bytes = None) -> str:

        if iv is None:
            iv = self.iv

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

        return decrypted_data.decode('utf-8')

    def get_iv(self) -> bytes:
        return self.iv

    def get_version(self) -> int:
        return self.version