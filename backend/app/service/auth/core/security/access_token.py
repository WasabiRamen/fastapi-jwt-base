# core/security/access_token.py
from datetime import datetime, timezone
import jwt
from pydantic import BaseModel, Field

class AccessTokenService:
    """JWT 생성 및 검증 유틸리티

    - HS256 알고리즘 사용
    - 토큰 만료 시간 설정 가능

    @TODO: 알고리즘 선택 기능 구현

    사용 예시:
    jwt_manager = JWTManager(algorithm=algorithm, access_token_expire_minutes=expire_minutes)
    기본값:
        algorithm = "HS256"
        access_token_expire_minutes = 15

    알고리즘은, 초기 셋팅 때만 건들 수 있게 설계 필요.
    """
    def __init__(self, algorithm: str = "HS256", access_token_expire_minutes: int = 15):
        allow_algorithms = ["HS256"]
        if algorithm not in allow_algorithms:
            raise AccessTokenService.NotSupportedAlgorithmError(f"지원하지 않는 알고리즘입니다. 지원 알고리즘: {allow_algorithms}")

        self.__ALGORITHM: str = algorithm
        self.__ACCESS_TOKEN_EXPIRE_MINUTES: int = access_token_expire_minutes

    # 예외 정의
    class ExpiredTokenError(Exception):
        """토큰 만료 예외"""
        pass

    class InvalidTokenError(Exception):
        """토큰 검증 예외"""
        pass

    class NotSupportedAlgorithmError(Exception):
        """지원하지 않는 알고리즘 예외"""
        pass

    class SecretKeyNotFoundError(Exception):
        """비밀 키 미설정 예외"""
        pass

    # 내부 응답 스키마 정의
    class TokenResponse(BaseModel):
        token: str = Field(..., description="JWT 토큰")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")

    # 내부 함수 정의
    @staticmethod
    def now() -> int:
        return round(datetime.now(timezone.utc).timestamp())

    # JWT 토큰 생성
    def issue_token(self, user_uuid: str, secret_key: str) -> TokenResponse:
        """
        JWT 토큰 생성
        
        @TODO: payload에 추가 클레임 삽입 기능 구현 
        1. permissions: 사용자 권한
        2. iss: 발급자
        """
        if not secret_key:
            raise AccessTokenService.SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

        sub = str(user_uuid)
        iat = self.now()  # 발급 시간
        exp = iat + self.__ACCESS_TOKEN_EXPIRE_MINUTES * 60 # 만료 시간

        payload = {
            "sub": sub,
            "iat": iat,
            "exp": exp
        }

        encoded_jwt = jwt.encode(payload, secret_key, algorithm=self.__ALGORITHM)
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode("utf-8")
        return AccessTokenService.TokenResponse(
            token=encoded_jwt,
            created_at=iat,
            expires_at=exp
        )

    # 각동 디코딩 로직
    def decode_token(self, token: str, secret_key: str | None = None, options: dict = None) -> dict:
        """
        JWT 디코딩. options에 verify_signature=False 가 명시되면 secret_key는 필수가 아님.
        """
        opts = options or {}
        verify_signature = opts.get("verify_signature", True)
        if verify_signature and not secret_key:
            raise AccessTokenService.SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

        try:
            payload = jwt.decode(
                token,
                key=(secret_key if verify_signature else None),
                algorithms=[self.__ALGORITHM],
                options=opts
            )
            return payload

        except Exception as e:
            # PyJWT의 ExpiredSignatureError가 있으면 별도 처리
            ExpiredErr = getattr(jwt, "ExpiredSignatureError", None)
            if ExpiredErr and isinstance(e, ExpiredErr):
                raise AccessTokenService.ExpiredTokenError("토큰이 만료되었습니다.") from e

            # 그 외 예외는 검증 실패로 래핑
            raise AccessTokenService.InvalidTokenError("토큰 검증에 실패하였습니다.") from e


    def decode_token_without_expiration(self, token: str, secret_key: str) -> dict:
        """만료 검증 없이 JWT 토큰 디코딩 및 payload 반환"""
        option = {
            "verify_exp": False
        }
        return self.decode_token(token, secret_key, option)
        
    def decode_token_without_validation(self, token: str) -> dict:
        """검증 없이 JWT 토큰 디코딩 및 payload 반환"""
        options = {
            "verify_signature": False,
            "verify_exp": False
            }
        return self.decode_token(token, None, options)