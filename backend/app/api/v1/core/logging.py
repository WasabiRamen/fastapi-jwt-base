from loguru import logger
import sys
from pathlib import Path

from app.core.settings import app_settings

# 로그 파일 디렉토리 생성
Path(app_settings.LOG_FILE_PATH).parent.mkdir(exist_ok=True)

# Loguru 기본 설정
logger.remove()  # 기본 핸들러 제거

console_format = (
    "<green>{time:YYYY-MM-DDTHH:mm:ss.SSSZZ}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[service]}</cyan> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level> "
    "{extra[request_id]} {extra[user_id]}"
)

logger.add(
    sys.stdout,
    level=app_settings.LOG_LEVEL,
    format=console_format,
    colorize=True,
    backtrace=True,
    diagnose=False,  # True면 개발 시 스택 추적을 더 많이 보여줌
)

# 파일: 구조화된 JSON 로그 (프로덕션 수집용)
# serialize=True => 한 줄당 JSON 출력 (NDJSON). 탐색/집계에 용이.
logger.add(
    app_settings.LOG_FILE_PATH,
    level=app_settings.LOG_LEVEL,
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    serialize=True,
    enqueue=True,    # 비동기 쓰기(프로덕션 권장)
)