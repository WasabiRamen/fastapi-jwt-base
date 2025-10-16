import re
from datetime import datetime, timedelta
from redis import asyncio as aioredis
from typing import Optional
from uuid import uuid4

import bcrypt
import jwt


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
