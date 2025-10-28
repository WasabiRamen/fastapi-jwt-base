from fastapi import HTTPException, status

class UserAlreadyExistsException(HTTPException):
    """이미 존재하는 사용자인 경우"""
    def __init__(self, user_id: str = None):
        detail = f"사용자 '{user_id}'는 이미 존재합니다." if user_id else "이미 존재하는 사용자 아이디입니다."
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )