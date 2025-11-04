from pydantic import BaseModel, Field, field_validator

class CreateUser(BaseModel):
    """
    사용자 생성 스키마
    
    user_id: 사용자 아이디
    password: 사용자 비밀번호 (8~16자, 대문자/숫자/특수문자 포함)
    """

    user_id: str = Field(..., description="아이디")
    password: str = Field(..., description="사용자 비밀번호 (8~16자, 대문자/숫자/특수문자 포함)")
    email: str = Field(..., description="이메일 주소")
    token: str | None = Field(None, description="이메일 인증 토큰")

    @field_validator('password')
    def password_policy(cls, v):
        if not (8 <= len(v) <= 16):
            raise ValueError('비밀번호는 8~16자여야 합니다.')
        if not any(c.isupper() for c in v):
            raise ValueError('대문자가 1개 이상 포함되어야 합니다.')
        if not any(c.isdigit() for c in v):
            raise ValueError('숫자가 1개 이상 포함되어야 합니다.')
        if not any(c in '!@#$%^&*' for c in v):
            raise ValueError('특수문자가 1개 이상 포함되어야 합니다.')
        return v
