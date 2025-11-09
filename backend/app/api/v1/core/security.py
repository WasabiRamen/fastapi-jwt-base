import re
import secrets
import hashlib
import httpx
from datetime import datetime, timezone
import bcrypt
import jwt
from pydantic import BaseModel, Field


# Password core utilities
# -----------------------------------------------------------------
class PasswordManager:
    """
    비밀번호 검증 및 해싱 유틸리티

    사용법:
        password_manager = PasswordManager(bcrypt_rounds=16)

    기본값:
        bcrypt_rounds: bcrypt 해싱 라운드 수 (기본값: 16)
    """
    def __init__(self, bcrypt_rounds: int = 16):
        self.__BCRYPT_ROUNDS: int = bcrypt_rounds
        self.__password_regex: str = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,16}$"
    

    class passwordValidationError(Exception):
        """비밀번호 정규식 실패 예외"""
        pass

    class passwordVerificationError(Exception):
        """비밀번호 검증 실패 예외"""
        pass


    def validate_password(self, plain_password: str) -> None:
        """비밀번호 정책(정규식) 검증"""
        if not re.fullmatch(self.__password_regex, plain_password):
            raise PasswordManager.passwordValidationError("비밀번호 정책에 맞지 않습니다.")

    def verify_password(self, plain_password: str, hashed_password: str) -> None:
        """평문 비밀번호와 해시를 비교합니다. bcrypt.checkpw는 안전한 비교를 수행합니다."""
        if not bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise PasswordManager.passwordVerificationError("비밀번호가 일치하지 않습니다.")

    def encrypt_password(self, plain_password: str) -> str:
        """
        비밀번호를 bcrypt로 해싱하여 utf-8 문자열로 반환합니다.
        """
        salt = bcrypt.gensalt(rounds=self.__BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        encode_hashed = hashed.decode('utf-8')
        return encode_hashed
    

# Token core utilities
# -----------------------------------------------------------------
    

class JWTManager:
    """JWT 생성 및 검증 유틸리티

    - HS256 알고리즘 사용
    - 토큰 만료 시간 설정 가능

    @TODO: 알고리즘 선택 기능 구현

    사용 예시:
    jwt_manager = JWTManager(algorithm=algorithm, access_token_expire_minutes=expire_minutes)
    기본값:
        algorithm = "HS256"
        access_token_expire_minutes = 15
    """
    def __init__(self, algorithm: str = "HS256", access_token_expire_minutes: int = 15):
        allow_algorithms = ["HS256"]
        if algorithm not in allow_algorithms:
            raise JWTManager.NotSupportedAlgorithmError(f"지원하지 않는 알고리즘입니다. 지원 알고리즘: {allow_algorithms}")

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

    # 해당 method tools로 이동
    # @classmethod
    # def get_secret_key(cls, app: FastAPI) -> str:
    #     """현재 앱 상태의 최신 JWT 비밀 키 반환"""
    #     return app.state.jwt_manager.current_secret.secret_key

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
            raise JWTManager.SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

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
        return JWTManager.TokenResponse(
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
            raise JWTManager.SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

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
                raise JWTManager.ExpiredTokenError("토큰이 만료되었습니다.") from e

            # 그 외 예외는 검증 실패로 래핑
            raise JWTManager.InvalidTokenError("토큰 검증에 실패하였습니다.") from e


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


class RefreshTokenManager:
    """
    리프래시 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 32바이트 랜덤 문자열

    사용법:
        refresh_token_manager = RefreshTokenManager(byte_length=32, store_hashed=True, expire_days=30)
    기본값:
        byte_length: 리프래시 토큰 바이트 길이 (기본값: 32)
        store_hashed: 토큰 저장 시 해싱 여부 (기본값: True)
        expire_days: 토큰 만료 기간 (기본값: 30일)
    """
    def __init__(self, byte_length: int = 32, store_hashed: bool = True, expire_days: int = 30):
        self.__REFRESH_TOKEN_BYTE_LENGTH = byte_length
        self.__REFRESH_TOKEN_STORE_HASHED = store_hashed
        self.__REFRESH_TOKEN_EXPIRE_DAYS = expire_days
    
    class TokenResponse(BaseModel):
        token: str = Field(..., description="리프래시 토큰")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
        user_uuid: str = Field(..., description="토큰 소유자 UUID (DB 저장용)")

    def get_expiration_datetime(self) -> tuple[int, int, int]:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = self.__REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    def create_token(self, user_uuid: str) -> TokenResponse:
        """CSPRNG 기반 리프래시 토큰 생성"""
        create_at, expires_at, expires_in = self.get_expiration_datetime()
        token = secrets.token_urlsafe(self.__REFRESH_TOKEN_BYTE_LENGTH)
        if self.__REFRESH_TOKEN_STORE_HASHED:
            token = hashlib.sha256(token.encode('utf-8')).hexdigest()
        return RefreshTokenManager.TokenResponse(
            token=token,
            created_at=create_at,
            expires_in=expires_in,
            expires_at=expires_at,
            user_uuid=user_uuid
        )

    def verify_token(self, token: str, stored_token: str) -> bool:
        """리프래시 토큰 검증"""
        if self.__REFRESH_TOKEN_STORE_HASHED:
            hash_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
            return hash_token == stored_token
        return token == stored_token
    

# Email core utilities
# -----------------------------------------------------------------


class EmailTokenManager:
    """
    이메일 인증 토큰 관리 유틸리티

    토큰 형식 -> CSPRNG 기반 16바이트 랜덤 문자열
    """
    def __init__(self, token_byte_length: int = 16, expire_minutes: int = 10):
        self.__EMAIL_TOKEN_BYTE_LENGTH = token_byte_length
        self.__EMAIL_TOKEN_EXPIRE_MINUTES = expire_minutes


    class EmailVerifyResponse(BaseModel):
        email: str = Field(..., description="이메일 주소")
        token: str = Field(..., description="이메일 인증 토큰")
        code: str = Field(..., description="이메일 인증 코드")
        expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
        created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
        expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")


    def get_expiration_datetime(self) -> tuple[int, int, int]:
        create_at = round(datetime.now(timezone.utc).timestamp())
        expires_in = self.__EMAIL_TOKEN_EXPIRE_MINUTES * 60
        expires_at = create_at + expires_in
        return create_at, expires_at, expires_in

    def create_token(self, email: str) -> EmailVerifyResponse:
        """CSPRNG 기반 이메일 인증 토큰 생성"""
        create_at, expires_at, expires_in = self.get_expiration_datetime()
        token = secrets.token_urlsafe(self.__EMAIL_TOKEN_BYTE_LENGTH)
        code = f"{secrets.randbelow(1000000):06d}"
        return EmailTokenManager.EmailVerifyResponse(
            email=email,
            token=token,
            code=code,
            expires_at=expires_at,
            created_at=create_at,
            expires_in=expires_in
        )


# Social core utilities
# -----------------------------------------------------------------

class GoogleOAuth2Manager:
    """
    구글 OAuth2 인증 유틸리티
    """
    def __init__(self, ux_mode: str = "popup", client_id: str = None, secret_key: str = None):
        allow_ux_modes = ["popup", "redirect"]
        if ux_mode not in allow_ux_modes:
            raise GoogleOAuth2Manager.UXModeError(f"지원하지 않는 UX 모드입니다. 지원 UX 모드: {allow_ux_modes}")

        if not client_id:
            raise GoogleOAuth2Manager.NotFoundClientIdError("구글 OAuth2 클라이언트 ID가 설정되지 않았습니다.")

        if not secret_key:
            raise GoogleOAuth2Manager.NotFoundSecretKeyError("구글 OAuth2 비밀 키가 설정되지 않았습니다.")

        self.__TOKEN_URL = "https://oauth2.googleapis.com/token"
        self.__USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.__CLIENT_ID = client_id
        self.__SECRET_KEY = secret_key
        self.__POPUP_REDIRECT_URI = "postmessage"
        self.__UX_MODE = ux_mode


    class UXModeError(Exception):
        """지원하지 않는 UX 모드 예외"""
        pass

    
    class NotFoundSecretKeyError(Exception):
        """구글 OAuth2 비밀 키 미설정 예외"""
        pass


    class NotFoundClientIdError(Exception):
        """구글 OAuth2 클라이언트 ID 미설정 예외"""
        pass

    class TokenRequestError(Exception):
        """구글 OAuth2 토큰 요청 실패 예외"""
        pass


    async def code_to_token(self, code: str, redirect_uri: str = None) -> dict:
        """
        구글 OAuth2 인증 코드로 액세스 토큰 요청
        """
        if self.__UX_MODE == "popup":
            redirect_uri = self.__POPUP_REDIRECT_URI
        elif self.__UX_MODE == "redirect":
            redirect_uri = redirect_uri
        else:
            raise GoogleOAuth2Manager.UXModeError("지원하지 않는 UX 모드입니다.")

        try:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(self.__TOKEN_URL, data={
                    "code": code,
                    "client_id": self.__CLIENT_ID,
                    "client_secret": self.__SECRET_KEY,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                })

                if token_response.status_code != 200:
                    raise GoogleOAuth2Manager.TokenRequestError("구글 OAuth2 토큰 요청에 실패하였습니다.")
                
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise GoogleOAuth2Manager.TokenRequestError("구글 액세스 토큰이 반환되지 않았습니다.")
                    
                # 2. 액세스 토큰으로 사용자 정보 요청
                user_response = await client.get(self.__USER_INFO_URL, headers={
                    "Authorization": f"Bearer {access_token}"
                })

                if user_response.status_code != 200:
                    raise GoogleOAuth2Manager.TokenRequestError("구글 OAuth2 사용자 정보 요청에 실패하였습니다.")

                return user_response.json()

        except httpx.RequestError as e:
            raise GoogleOAuth2Manager.TokenRequestError("구글 OAuth2 요청 중 네트워크 오류가 발생했습니다.") from e

