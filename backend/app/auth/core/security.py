import re
import secrets
import hashlib
from datetime import datetime, timezone

import bcrypt
import jwt
from fastapi import FastAPI

from app.auth.setting import setting
from app.auth.schemas import AccessTokenResponse, RefreshTokenResponse, EmailVerifyResponse

password_regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,16}$"


class PasswordManager:
    """
    비밀번호 검증 및 해싱 유틸리티

    @Todo: BCRYPT 라운드를 환경변수로 설정 가능
    @Todo: 입력 길이 제한으로 DoS 완화
    @Todo: optional server-side PEPPER 지원 (환경변수 PASSWORD_PEPPER)
    @Todo: verify_password에서 예외 처리
    """

    BCRYPT_ROUNDS: int = setting.BCRYPT_ROUNDS

    @staticmethod
    def validate_password(plain_password: str) -> bool:
        """비밀번호 정책(정규식) 검증"""
        return re.fullmatch(password_regex, plain_password) is not None

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해시를 비교합니다. bcrypt.checkpw는 안전한 비교를 수행합니다."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def encrypt_password(plain_password: str) -> str:
        """
        비밀번호를 bcrypt로 해싱하여 utf-8 문자열로 반환합니다.
        """
        salt = bcrypt.gensalt(rounds=PasswordManager.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        encode_hashed = hashed.decode('utf-8')
        return encode_hashed
    

class JWTManager:
    """JWT 생성 및 검증 유틸리티

    - HS256 알고리즘 사용
    - 토큰 만료 시간 설정 가능
    """

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = setting.ACCESS_TOKEN_EXPIRE_MINUTES

    @classmethod
    def get_secret_key(cls, app: FastAPI) -> str:
        """현재 앱 상태의 최신 JWT 비밀 키 반환"""
        return app.state.jwt_manager.current_secret.secret_key


    @classmethod
    def create_token(cls, user_uuid: str, app: FastAPI) -> AccessTokenResponse:
        """JWT 토큰 생성"""

        sub = str(user_uuid)
        iat = round(datetime.now(timezone.utc).timestamp())
        exp = iat + cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        payload = {
            "sub": sub,
            "iat": iat,
            "exp": exp
        }

        secret_key = cls.get_secret_key(app)

        encoded_jwt = jwt.encode(payload, secret_key, algorithm=cls.ALGORITHM)
        return AccessTokenResponse(
            token=encoded_jwt,
            expires_in=exp,
            expires_at=iat
        )

    @classmethod
    def verify_token(cls, token: str, app: FastAPI) -> dict:
        """JWT 토큰 검증 및 payload 반환. 실패 시 예외 발생"""
        try:
            payload = jwt.decode(token, cls.get_secret_key(app), algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("토큰이 만료되었습니다.")
        except jwt.InvalidTokenError:
            raise ValueError("유효하지 않은 토큰입니다.")
    
    @classmethod
    def decode_token_without_expiration(cls, token: str, app: FastAPI) -> dict:
        """검증 없이 JWT 토큰 디코딩 및 payload 반환"""
        try:
            payload = jwt.decode(token, cls.get_secret_key(app), algorithms=[cls.ALGORITHM], options={"verify_exp": False})
            return payload
        except jwt.InvalidTokenError:
            raise ValueError("유효하지 않은 토큰입니다.")

    @classmethod
    def decode_token_without_validation(cls, token: str, app: FastAPI) -> dict:
        """검증 없이 JWT 토큰 디코딩 및 payload 반환"""
        try:
            options = {"verify_signature": False, "verify_exp": False}
            payload = jwt.decode(token, cls.get_secret_key(app), algorithms=[cls.ALGORITHM], options=options)
            return payload
        except jwt.InvalidTokenError:
            raise ValueError("유효하지 않은 토큰입니다.")
  

class RefreshTokenManager:
    """
    리프래시 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 32바이트 랜덤 문자열
    """
    REFRESH_TOKEN_BYTE_LENGTH = setting.REFRESH_TOKEN_BYTE_LENGTH
    REFRESH_TOKEN_STORE_HASHED = setting.REFRESH_TOKEN_STORE_HASHED  # 해시 저장 여부 설정
    REFRESH_TOKEN_EXPIRE_DAYS = setting.REFRESH_TOKEN_EXPIRE_DAYS  # 리프래시 토큰 만료 기간 (일)

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
        token = secrets.token_urlsafe(cls.REFRESH_TOKEN_BYTE_LENGTH)
        if cls.REFRESH_TOKEN_STORE_HASHED:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token
        return RefreshTokenResponse(
            token=token,
            created_at=create_at,
            expires_at=expires_at,
            expires_in=expires_in,
            user_uuid=user_uuid
        )

    @classmethod
    def verify_token(cls, token: str, stored_token: str) -> bool:
        """리프래시 토큰 검증"""
        if cls.REFRESH_TOKEN_STORE_HASHED:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token == stored_token
        return token == stored_token


class EmailTokenManager:
    """
    이메일 인증 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 16바이트 랜덤 문자열
    """
    EMAIL_TOKEN_BYTE_LENGTH = setting.EMAIL_VERIFY_CODE_LENGTH
    EMAIL_TOKEN_EXPIRE_MINUTES = setting.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES  # 이메일 토큰 만료 기간 (분)

    @staticmethod
    def get_expiration_datetime() -> datetime:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = EmailTokenManager.EMAIL_TOKEN_EXPIRE_MINUTES * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    @classmethod
    def generate_6digit_code(cls) -> str:
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def create_token(cls, email: str) -> EmailVerifyResponse:
        """CSPRNG 기반 이메일 인증 토큰 생성"""
        create_at, expires_at, expires_in = cls.get_expiration_datetime()
        token = secrets.token_urlsafe(cls.EMAIL_TOKEN_BYTE_LENGTH)
        code = cls.generate_6digit_code()
        return EmailVerifyResponse(
            email=email,
            token=token,
            code=code,
            created_at=create_at,
            expires_at=expires_at,
            expires_in=expires_in
        )


