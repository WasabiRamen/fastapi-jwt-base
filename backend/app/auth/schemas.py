from pydantic import BaseModel, Field


# class LoginUser(BaseModel): -> OAuth2PasswordRequestForm대체
#     """
#     사용자 로그인 스키마
    
#     user_id: 사용자 아이디
#     password: 사용자 비밀번호
#     """

#     user_id: str = Field(..., description="아이디")
#     password: str = Field(
#         ..., pattern=password_regex, 
#         description="사용자 비밀번호 (8~16자, 대문자/숫자/특수문자 포함)"
#         )


# ----------------------------------------------------------------

# 내부 로직에서 사용하는 응답 스키마 정의
class AccessTokenResponse(BaseModel):
    token : str = Field(..., description="JWT 액세스 토큰")
    expires_in : int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at : int = Field(..., description="토큰 만료 시간(Unix timestamp)")


class RefreshTokenResponse(BaseModel):
    token: str = Field(..., description="리프래시 토큰")
    created_at: int = Field(..., description="토큰 생성 시간(Unix timestamp)")
    expires_in: int = Field(..., description="토큰 만료까지 남은 시간(초)")
    expires_at: int = Field(..., description="토큰 만료 시간(Unix timestamp)")
    user_uuid: str = Field(..., description="토큰 소유자 UUID (DB 저장용)")