# fastapi-jwt-p1

🚀 JWT 인증, OAuth2.0 지원, Refresh Token Rotation이 구현된 프로덕션 준비 완료 FastAPI 보일러플레이트

## 주요 기능

- 🔐 **OAuth2.0 Password Grant** - 표준 OAuth2.0 인증 플로우
- 🔁 **Refresh Token Rotation** - 토큰 갱신 시마다 회전하여 보안 강화
- 🍪 **HTTP-only 쿠키** - 쿠키를 통한 안전한 토큰 저장
- 🗄️ **PostgreSQL + SQLAlchemy** - SQLAlchemy 2.0을 활용한 비동기 데이터베이스 작업
- ⚡ **Redis 연동** - 토큰 블랙리스트 및 캐싱 지원
- 🧰 **클린 아키텍처** - 체계적으로 구성된 프로젝트 구조
- 📦 **Docker 지원** - 컨테이너화된 개발을 위한 Dev Container 지원

## 기술 스택

- [FastAPI](https://fastapi.tiangolo.com/) - 현대적인 Python 웹 프레임워크
- [PyJWT](https://pyjwt.readthedocs.io/) - JSON Web Token 구현
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) - 비동기 ORM
- [PostgreSQL](https://www.postgresql.org/) - 데이터베이스
- [Redis](https://redis.io/) - 캐싱 및 세션 관리
- [Uvicorn](https://www.uvicorn.org/) - ASGI 서버

## 시작하기

### 사전 요구사항

- Python 3.11+
- PostgreSQL
- Redis

### 설치 방법

```bash
# 1. 저장소 복제
git clone https://github.com/WasabiRamen/fastapi-jwt-p1.git
cd fastapi-jwt-p1

# 2. 의존성 설치
cd backend
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일을 수정하여 설정 입력

# 4. 서버 실행
uvicorn main:app --reload
```

### 환경 변수

```env
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 인증 플로우

1. **회원가입** (`POST /api/v1/accounts/`)
   - account_id와 password로 새 계정 생성

2. **로그인** (`POST /api/v1/accounts/token`)
   - 사용자 자격 증명 제공
   - Access Token (30분) + Refresh Token (7일) 수령
   - 토큰은 HTTP-only 쿠키에 저장됨

3. **토큰 갱신** (`POST /api/v1/accounts/refresh`)
   - Refresh Token을 사용하여 새 Access Token 발급
   - 기존 Refresh Token은 무효화 (Token Rotation)
   - 새로운 토큰 쌍 발급

4. **로그아웃** (`DELETE /api/v1/accounts/logout`)
   - 데이터베이스에서 Refresh Token 무효화
   - 쿠키 삭제

5. **보호된 라우트**
   - Authorization 헤더 또는 쿠키에 Access Token 필요
   - 매 요청마다 토큰 유효성 검증

## API 엔드포인트

### 인증

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| POST | `/api/v1/accounts/token` | 로그인 및 토큰 발급 |
| POST | `/api/v1/accounts/refresh` | 액세스 토큰 갱신 |
| DELETE | `/api/v1/accounts/logout` | 로그아웃 및 토큰 무효화 |

### 계정 관리

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| POST | `/api/v1/accounts/` | 새 계정 생성 |
| GET | `/api/v1/accounts/me` | 현재 사용자 정보 조회 |
| GET | `/api/v1/accounts/exist/{user_id}` | 사용자 ID 중복 확인 |
| POST | `/api/v1/accounts/verify_password` | 비밀번호 검증 |
| PUT | `/api/v1/accounts/password` | 비밀번호 변경 |

### 헬스 체크

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| GET | `/health` | Redis 연결 확인 |
| GET | `/` | 루트 엔드포인트 |

## 프로젝트 구조

```
.
├── backend/
│   ├── main.py                 # 애플리케이션 진입점
│   ├── requirements.txt        # Python 의존성
│   └── app/
│       ├── api/
│       │   └── v1/
│       │       └── account.py  # 계정 엔드포인트
│       ├── core/
│       │   ├── database.py     # 데이터베이스 연결
│       │   ├── redis.py        # Redis 연결
│       │   ├── security.py     # JWT 및 비밀번호 처리
│       │   └── cookie.py       # 쿠키 관리
│       ├── crud/
│       │   └── account.py      # 데이터베이스 작업
│       ├── models/
│       │   └── account.py      # SQLAlchemy 모델
│       └── schemas/
│           └── account.py      # Pydantic 스키마
├── .devcontainer/              # Dev Container 설정
└── README.md
```

## 보안 기능

### 구현 완료 ✅

- ✅ **Refresh Token Rotation** - 토큰 사용 후 무효화
- ✅ **비밀번호 해싱** - bcrypt를 사용한 안전한 비밀번호 저장
- ✅ **HTTP-only 쿠키** - XSS 공격 방어
- ✅ **토큰 만료** - 짧은 수명의 액세스 토큰
- ✅ **데이터베이스 토큰 검증** - 서버 측 토큰 검증
- ✅ **IP & User-Agent 추적** - 토큰 사용 모니터링

### 프로덕션 권장 사항 🔧

- 🔧 **Rate Limiting** - 무차별 대입 공격 방지
- 🔧 **CORS 설정** - 허용된 출처 제한
- 🔧 **CSRF 보호** - 쿠키 기반 인증을 위한 보호
- 🔧 **토큰 정리** - 만료된 토큰 정리 크론잡
- 🔧 **입력 검증** - 강화된 스키마 검증
- 🔧 **로깅 & 모니터링** - 요청/에러 로깅

## 사용 예제

### 새 사용자 등록

```bash
curl -X POST "http://localhost:8000/api/v1/accounts/" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "john", "password": "securepass123"}'
```

### 로그인

```bash
curl -X POST "http://localhost:8000/api/v1/accounts/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john&password=securepass123" \
  -c cookies.txt
```

### 보호된 엔드포인트 접근

```bash
curl -X GET "http://localhost:8000/api/v1/accounts/me" \
  -b cookies.txt
```

### 토큰 갱신

```bash
curl -X POST "http://localhost:8000/api/v1/accounts/refresh" \
  -b cookies.txt \
  -c cookies.txt
```

### 로그아웃

```bash
curl -X DELETE "http://localhost:8000/api/v1/accounts/logout" \
  -b cookies.txt
```

## 개발

### Docker로 실행

```bash
# VS Code의 Dev Container 확장으로 열기
# 컨테이너가 자동으로 PostgreSQL과 Redis 설정
```

### 테스트 실행

```bash
# TODO: pytest 설정 추가
pytest
```

## 라이선스

MIT License

## 기여하기

기여를 환영합니다! Pull Request를 자유롭게 제출해 주세요.

## 감사의 말

- [FastAPI](https://fastapi.tiangolo.com/)로 구축됨
- OAuth2.0 모범 사례에서 영감을 받음
- OWASP 보안 가이드라인 준수

---

본 README.md는 GitHub Copilot으로 작성되었습니다!