# auth/tools/rsa_keys/generator.py
"""
RSA 키 쌍 생성기 유틸리티
"""

# Standard Library
from datetime import datetime, timezone
from uuid import uuid4

# Pydantic
from pydantic import BaseModel, Field

# Cryptography
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class RSAKeyPair(BaseModel):
    """
    RSA 키 쌍 모델

    Attributes:
        private_key: str, PEM 형식의 RSA 개인키
        public_key: str, PEM 형식의 RSA 공개키

    # 만료일은 여기서 설정 X -> 스케줄 기반 로테이션 로직에서 구현
    """
    kid: str = Field(..., description="키 식별자 (Key ID)")
    private_key: str = Field(..., description="PEM 형식의 RSA 개인키")
    public_key: str = Field(..., description="PEM 형식의 RSA 공개키")
    created_at: int = Field(..., description="키 생성 일시 (Timestamp)")


def generate_kid(created_at: int) -> str:
    """
    RSA KEY ID 생성 유틸

    키 형식 - yyyy-mm-dd_uuid4
    """
    created_date = datetime.fromtimestamp(created_at, timezone.utc).strftime("%Y-%m-%d")
    kid = f"rsa-{created_date}-{str(uuid4())}"
    return kid


def generate_rsa_key_pair() -> RSAKeyPair:    
    """
    RSA 키 쌍 생성 유틸 함수
    """
    # 1. RSA 개인키 생성 (2048bit)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        )

    # 2. 개인키를 PEM 문자열로 내보내기
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # 3. 공개키를 PEM 문자열로 내보내기
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    created_at = int(datetime.now(timezone.utc).timestamp())
    kid = generate_kid(created_at)

    return RSAKeyPair(
        kid=kid,
        private_key=private_pem,
        public_key=public_pem,
        created_at=created_at
    )


async def key_save(file_path: str, key_string: str) -> None:
    """
    RSA 개인키를 PEM 파일로 저장하는 유틸 함수

    Args:
        file_path (str): PEM 파일 경로
    """
    if not file_path.endswith(".pem"):
        raise ValueError("file_path 확장자는 .pem 이어야 합니다.")
    
    with open(file_path, "w") as f:
        f.write(key_string)
    