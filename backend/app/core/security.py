import re
import secrets
import hashlib
from datetime import datetime, timezone

import bcrypt
import jwt
from pydantic import BaseModel, Field
from typing import Optional


class AccessTokenResponse(BaseModel):
    token : str = Field(..., description="JWT 액세스 토큰")
    expires_in : int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at : int = Field(..., description="토큰 만료 시간(Unix timestamp)")


class RefreshTokenResponse(BaseModel):
    token: str = Field(..., description="리프래시 토큰")
    create_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
    expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
    uuid: Optional[str] = Field(..., description="토큰 소유자 UUID (DB 저장용)")


class PasswordManager:
    """비밀번호 검증 및 해싱 유틸리티

    - 요구사항: 대문자 1개 이상, 숫자 1개 이상, 특수문자 1개 이상,
      영어(영문자) 포함, 길이 8~16
    - bcrypt로 해싱 (라운드 설정 가능)
    """

    BCRYPT_ROUNDS: int = 12

    __PASSWORD_RE = re.compile(r'''
        ^                                                   # 문자열 시작
        (?=.*[A-Z])                                         # 최소 한 개의 대문자
        (?=.*\d)                                           # 최소 한 개의 숫자
        (?=.*[!@#$%^&*()_+\-=\[\]{};:'"\\|,.<>\/\?`~]) # 최소 한 개의 허용 특수문자
        [A-Za-z\d!@#$%^&*()_+\-=\[\]{};:'"\\|,.<>\/\?`~] # 허용 문자 집합
        {8,16}                                              # 길이 8~16자
        $                                                   # 문자열 끝
    ''', re.VERBOSE)

    @staticmethod
    def _is_valid_password(password: str) -> bool:
        """간단한 True/False 검증. 내부용; 상세 실패 원인은 `validate_password` 사용 권장."""
        return bool(PasswordManager.__PASSWORD_RE.match(password))

    @staticmethod
    def validate_password(password: str):
        """비밀번호가 왜 실패하는지에 대한 상세 정보를 반환합니다.

        반환: (is_valid: bool, errors: list[str])
        """
        errors = []
        if not (8 <= len(password) <= 16):
            errors.append("길이는 8자 이상 16자 이하이어야 합니다.")
        if not re.search(r"[A-Z]", password):
            errors.append("최소 한 개의 대문자(A-Z)가 필요합니다.")
        if not re.search(r"\d", password):
            errors.append("최소 한 개의 숫자(0-9)가 필요합니다.")
        if not re.search(r"[A-Za-z]", password):
            errors.append("최소 한 개의 영어 문자가 필요합니다.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};:'\"\\|,.<>\/\?`~]", password):
            errors.append("최소 한 개의 특수문자가 필요합니다.")
        # 허용 문자만 포함되었는지 확인
        if re.search(r"[^A-Za-z\d!@#$%^&*()_+\-=\[\]{};:'\"\\|,.<>\/\?`~]", password):
            errors.append("허용되지 않는 문자가 포함되어 있습니다.")

        return (len(errors) == 0, errors)

    @staticmethod
    def encrypt_password(plain_password: str) -> str:
        """비밀번호를 bcrypt로 해싱하여 utf-8 문자열로 반환합니다.

        비밀번호 검증 실패 시 ValueError 발생.
        """
        if not PasswordManager._is_valid_password(plain_password):
            raise ValueError(
                "비밀번호는 8~16자, 최소 한 개의 대문자, 숫자, 특수문자를 포함해야 합니다."
            )
        salt = bcrypt.gensalt(rounds=PasswordManager.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        encode_hashed = hashed.decode('utf-8')
        return encode_hashed

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해시를 비교합니다. bcrypt.checkpw는 안전한 비교를 수행합니다."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    

class JWTManager:
    """JWT 생성 및 검증 유틸리티

    - HS256 알고리즘 사용
    - 토큰 만료 시간 설정 가능
    """

    SECRET_KEY = '3tL5qvicpGKyTJ0yyooss7lEAh+iZ075pW+J+Y3n32o='
    # SECRET_KEY_ROTATION_DAYS = 30 # 아직 비밀키 교체 로직 미구현

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 기본 만료 시간(분)

    def __init__(self):
        pass

    @staticmethod
    def _secret_key_rotation() -> None:
        pass


    @classmethod
    def create_token(cls, uuid: str) -> AccessTokenResponse:
        """JWT 토큰 생성"""

        sub = str(uuid)
        iat = round(datetime.now(timezone.utc).timestamp())
        exp = iat + cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        payload = {
            "sub": sub,
            "iat": iat,
            "exp": exp
        }

        encoded_jwt = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return AccessTokenResponse(
            token = encoded_jwt,
            expires_in = exp,
            expires_at = iat
            )

    @classmethod
    def verify_token(cls, token: str) -> dict:
        """JWT 토큰 검증 및 payload 반환. 실패 시 예외 발생"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("토큰이 만료되었습니다.")
        except jwt.InvalidTokenError:
            raise ValueError("유효하지 않은 토큰입니다.")
        

class RefreshTokenManager:
    """
    리프래시 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 32바이트 랜덤 문자열
    """
    TOKEN_BYTE_LENGTH = 32
    STORE_HASHED_REFRESH_TOKENS = False  # 해시 저장 여부 설정
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 리프래시 토큰 만료 기간 (일)

    @staticmethod
    def get_expiration_datetime() -> datetime:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = RefreshTokenManager.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    @classmethod
    def create_token(cls, user_uuid: str = None) -> RefreshTokenResponse:
        """CSPRNG 기반 리프래시 토큰 생성"""
        create_at, expires_at, expires_in = cls.get_expiration_datetime()
        token = secrets.token_urlsafe(cls.TOKEN_BYTE_LENGTH)
        if cls.STORE_HASHED_REFRESH_TOKENS:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token
        return RefreshTokenResponse(
            token=token,
            create_at=create_at,
            expires_at=expires_at,
            expires_in=expires_in,
            uuid=user_uuid
        )

    @classmethod
    def verify_token(cls, token: str, stored_token: str) -> bool:
        """리프래시 토큰 검증"""
        if cls.STORE_HASHED_REFRESH_TOKENS:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token == stored_token
        return token == stored_token