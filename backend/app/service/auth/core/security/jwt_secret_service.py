import os
import secrets
import json
import asyncio
from loguru import logger

from datetime import datetime, timezone
from pydantic import Field, BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class JWTSecretService:
    """
    로컬 JWT 비밀 키 관리 유틸

    차후 AWS로 관리하는 로직도 가져오겠음.

    Lifespan에 추가하면 바로 사용 가능.

    예제:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.jwt_manager = JWTSecretService()
    """
    class JWTSecret(BaseModel):
        secret_key: str = Field(..., description="JWT 비밀 키")
        created_at: int = Field(..., description="JWT 비밀 키 생성 시간")
        expired_at: int = Field(..., description="JWT 비밀 키 만료 시간")

    class setting(BaseModel):
        SECRET_KEY_PATH: str = Field("./jwt_secret_key.json", description="JWT 비밀 키 파일 경로")
        SECRET_KEY_ROTATION_DAYS: int = Field(30, description="JWT 비밀 키 회전 주기(일)")


    def __init__(self, key_path: str = None, rotation_days: int = None, rsa_mode: bool = False):
        # 무거운 작업은 init()으로 옮김: 생성자는 빠르게 반환
        self.scheduler = AsyncIOScheduler()
        self.current_secret = None
        self.__KEY_PATH = key_path
        self.__ROTATION_DAYS = rotation_days
        self.__RSA_MODE = rsa_mode

        if not self.__KEY_PATH.startswith('/'):
            self.__KEY_PATH = os.path.join(os.getcwd(), self.__KEY_PATH)

    async def init(self) -> None:
        """
        비동기 초기화: 파일 I/O 같은 블로킹 작업은 스레드로 실행.
        lifespan에서 반드시 await manager.init() 호출할 것.
        """
        # _load_or_create_key 는 현재 동기 함수이므로 to_thread로 실행
        self.current_secret = await asyncio.to_thread(self._load_or_create_key)
        # 스케줄 등록/시작은 이벤트루프 친화적으로 수행
        self._schedule_next_rotation() 

    def _now_ts(self) -> int:
        return int(datetime.now(tz=timezone.utc).timestamp())

    def _generate_new_key(self) -> JWTSecret:
        now = self._now_ts()
        if self.__RSA_MODE:
            # RSA 키 쌍 생성 로직 추가 예정
            pass
        return self.JWTSecret(
            secret_key=secrets.token_hex(32),
            created_at=now,
            expired_at=now + self.__ROTATION_DAYS * 86400
        )

    def _key_file_exists(self) -> bool:
        return os.path.exists(self.__KEY_PATH)

    def _save_key(self, jwt_secret: JWTSecret):
        with open(self.__KEY_PATH, 'w') as f:
            json.dump(jwt_secret.model_dump(), f)

    def _load_or_create_key(self) -> JWTSecret:
        if not self._key_file_exists():
            key = self._generate_new_key()
            self._save_key(key)
            return key

        with open(self.__KEY_PATH) as f:
            data = json.load(f)
            key = self.JWTSecret.model_validate(data)
            if self._now_ts() >= key.expired_at:
                key = self._generate_new_key()
                self._save_key(key)
        return key

    def rotate_key(self) -> None:
        if self.current_secret.expired_at < self._now_ts():
            key = self._generate_new_key()
            self._save_key(key)
            self.current_secret = key

    def _schedule_next_rotation(self):
        run_date = datetime.fromtimestamp(self.current_secret.expired_at, tz=timezone.utc)
        self.scheduler.add_job(self.rotate_key, "date", run_date=run_date)
        if not self.scheduler.running:
            self.scheduler.start()
        logger.info(f"다음 키 회전 예약: {run_date}")