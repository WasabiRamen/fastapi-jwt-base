# FastAPI Backend Load Testing with Locust

이 디렉토리는 FastAPI 백엔드 API의 부하 테스트를 위한 Locust 스크립트를 포함합니다.

## 📋 테스트 대상 API

1. **`POST /auth/token`** - 로그인 및 토큰 발급
2. **`GET /accounts/me`** - 현재 사용자 정보 조회 (인증 필요)

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정 - 테스트 계정 정보 입력
# TEST_USERNAME=your_test_user
# TEST_PASSWORD=your_test_password
```

### 3. 테스트 실행

#### 방법 1: Web UI 사용 (권장)

```bash
# Locust Web UI 시작
locust -f locustfile.py --host=http://localhost:8000

# 브라우저에서 http://localhost:8089 접속
# - Number of users: 시뮬레이션할 사용자 수
# - Spawn rate: 초당 생성할 사용자 수
```

#### 방법 2: CLI 모드 (헤드리스)

```bash
# 10명의 사용자, 초당 2명씩 증가, 1분간 실행
locust -f locustfile.py --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 1m \
  --headless

# 결과를 CSV로 저장
locust -f locustfile.py --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless \
  --csv=results/load_test_$(date +%Y%m%d_%H%M%S)
```

#### 방법 3: Docker 환경에서 실행

```bash
# Backend 서비스가 docker-compose로 실행 중인 경우
locust -f locustfile.py --host=http://localhost:8000
```

## 📊 테스트 시나리오

### AuthenticatedUser (기본 사용자)
실제 사용자 행동을 시뮬레이션:
- **로그인**: 테스트 시작 시 한 번 실행
- **사용자 정보 조회** (가중치: 5): 가장 자주 실행되는 작업
- **토큰 갱신** (가중치: 1): 주기적으로 실행

### LoginOnlyUser (로그인 전용)
인증 엔드포인트의 부하 테스트:
- **로그인**: 반복적으로 로그인만 수행

## 🔧 사용자 정의

### 특정 User 클래스만 실행

```bash
# AuthenticatedUser만 실행
locust -f locustfile.py --host=http://localhost:8000 AuthenticatedUser

# LoginOnlyUser만 실행
locust -f locustfile.py --host=http://localhost:8000 LoginOnlyUser
```

### 태스크 가중치 조정

`locustfile.py`에서 `@task(N)` 데코레이터의 값을 변경:
```python
@task(10)  # 가중치를 10으로 증가 (더 자주 실행)
def get_current_user(self):
    ...
```

### 대기 시간 조정

```python
# 요청 간 1-5초 대기
wait_time = between(1, 5)
```

## 📈 결과 분석

### Web UI에서 확인 가능한 지표:
- **Requests/s**: 초당 요청 수
- **Response Time**: 응답 시간 (평균, 중앙값, 95%, 99%)
- **Failures**: 실패한 요청 비율
- **Number of Users**: 현재 활성 사용자 수

### CSV 결과 파일:
```bash
results/
├── load_test_YYYYMMDD_HHMMSS_stats.csv          # 요청 통계
├── load_test_YYYYMMDD_HHMMSS_stats_history.csv  # 시간별 통계
└── load_test_YYYYMMDD_HHMMSS_failures.csv       # 실패 기록
```

## 🔍 문제 해결

### 로그인 실패
1. `.env` 파일의 `TEST_USERNAME`과 `TEST_PASSWORD` 확인
2. 데이터베이스에 해당 계정이 존재하는지 확인
3. Backend 서버가 실행 중인지 확인

### 인증 오류 (401 또는 500)
**가장 흔한 문제**: HTTP 연결에서 Secure 쿠키 사용

1. `backend/app/settings/.env.dev` 파일 확인
2. `COOKIE_SECURE=False`로 설정 (HTTP 테스트 시)
3. Backend 서버 재시작
   ```bash
   # backend 디렉토리에서
   ./run_app.sh
   ```

### 토큰 만료 에러
- 스크립트는 자동으로 토큰 갱신을 시도합니다
- 만료 시간이 너무 짧은 경우 Backend 설정 확인

### 연결 에러
```bash
# Backend 서버 상태 확인
curl http://localhost:8000/health

# Docker 컨테이너 확인
docker-compose ps
```

## 📝 테스트 전 체크리스트

- [ ] Backend 서버가 실행 중
- [ ] 테스트 계정이 데이터베이스에 존재
- [ ] `.env` 파일에 올바른 credentials 설정
- [ ] Database와 Redis가 실행 중
- [ ] 필요한 Python 패키지 설치 완료
- [ ] **중요**: HTTP 테스트 시 `backend/app/settings/.env.dev`에서 `COOKIE_SECURE=False` 설정

### ⚠️ HTTPS vs HTTP 설정

Backend API가 HTTP (`http://localhost:8000`)로 실행 중인 경우:
```bash
# backend/app/settings/.env.dev 파일 수정
COOKIE_SECURE=False
```

Backend API가 HTTPS로 실행 중인 경우:
```bash
# backend/app/settings/.env.dev 파일
COOKIE_SECURE=True

# locust도 HTTPS로 테스트
locust -f locustfile.py --host=https://your-domain.com
```

**이유**: `COOKIE_SECURE=True`일 때 쿠키는 HTTPS 연결에서만 전송됩니다. HTTP 연결에서는 인증 쿠키가 전송되지 않아 `/accounts/me` 등의 인증이 필요한 엔드포인트에서 500 에러가 발생합니다.

## 🎯 권장 테스트 시나리오

### 1. 기본 부하 테스트
```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 20 --spawn-rate 2 --run-time 2m --headless
```

### 2. 스트레스 테스트 (높은 부하)
```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m --headless
```

### 3. 스파이크 테스트 (급격한 부하 증가)
```bash
locust -f locustfile.py --host=http://localhost:8000 \
  --users 200 --spawn-rate 50 --run-time 1m --headless
```

## 📚 추가 리소스

- [Locust 공식 문서](https://docs.locust.io/)
- [부하 테스트 모범 사례](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [FastAPI 성능 최적화](https://fastapi.tiangolo.com/deployment/concepts/)

## 🐛 이슈 및 개선사항

이슈가 있거나 개선 아이디어가 있다면 GitHub Issues에 등록해 주세요.
