import app.accounts.crud as crud
import app.auth.core.security as security
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.exceptions import (
    UserAlreadyExistsException, 
    )

from app.auth.exceptions import InvalidPasswordException


async def create_user(db: AsyncSession, user_id: str, password: str) -> bool:
    """
    사용자 생성 서비스

    user_id: 사용자 아이디
    password: 사용자 비밀번호

    아이디 중복 검사 및 비밀번호 정책 검증 후 사용자 생성
    """
    exist_user = await crud.get_user_by_user_id(db, user_id)
    if exist_user:
        raise UserAlreadyExistsException(user_id=user_id)
    
    password_valid = security.PasswordManager.validate_password(password)
    if not password_valid:
        raise InvalidPasswordException()

    return await crud.create_user(db, user_id, password)