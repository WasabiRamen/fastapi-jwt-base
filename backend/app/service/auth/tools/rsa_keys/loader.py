from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import asyncio

async def load_private_key(file_path: str) -> rsa.RSAPrivateKey:
    """
    PEM 파일에서 RSA 개인키 불러오기
    """
    def _read_key():
        with open(file_path, "rb") as f:
            return f.read()

    key_bytes = await asyncio.to_thread(_read_key)

    private_key = serialization.load_pem_private_key(
        key_bytes,
        password=None,
    )
    return private_key


async def load_public_key(file_path: str) -> str:
    """
    PEM 파일에서 RSA 공개키 불러오기
    """
    def _read_key():
        with open(file_path, "rb") as f:
            return f.read()

    key_bytes = await asyncio.to_thread(_read_key)

    return key_bytes.decode('utf-8')