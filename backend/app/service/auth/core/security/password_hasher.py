import re
import bcrypt

class PasswordHasher:
    """
    비밀번호 검증 및 해싱 유틸리티

    사용법:
        password_hasher = PasswordHasher(bcrypt_rounds=16)

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
            raise PasswordHasher.passwordValidationError("비밀번호 정책에 맞지 않습니다.")

    def verify_password(self, plain_password: str, hashed_password: str) -> None:
        """평문 비밀번호와 해시를 비교합니다. bcrypt.checkpw는 안전한 비교를 수행합니다."""
        if not bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise PasswordHasher.passwordVerificationError("비밀번호가 일치하지 않습니다.")

    def hash_password(self, plain_password: str) -> str:
        """
        비밀번호를 bcrypt로 해싱하여 utf-8 문자열로 반환합니다.
        """
        salt = bcrypt.gensalt(rounds=self.__BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        encode_hashed = hashed.decode('utf-8')
        return encode_hashed