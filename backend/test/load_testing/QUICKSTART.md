# Quick Start Guide - Locust Load Testing

## 🚀 3단계로 시작하기

### 1️⃣ 의존성 설치
```bash
cd /workspaces/FastAPI-MSA-Ready-Template/backend/test/load_testing
source ../venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ 환경 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (테스트 계정 정보 입력)
# TEST_USERNAME=testuser
# TEST_PASSWORD=TestPass123!
```

### 3️⃣ 테스트 실행

**방법 A: Helper 스크립트 사용 (권장)**
```bash
# Web UI로 실행
./run_test.sh --web

# CLI로 빠른 테스트
./run_test.sh -u 10 -r 2 -t 1m

# 결과를 CSV로 저장
./run_test.sh -u 50 -r 5 -t 2m -o ./results
```

**방법 B: Locust 직접 실행**
```bash
# Web UI 시작
locust -f locustfile.py --host=http://localhost:8000

# 헤드리스 모드
locust -f locustfile.py --host=http://localhost:8000 \
  --users 20 --spawn-rate 2 --run-time 1m --headless
```

## 📊 Web UI 사용법

1. 브라우저에서 `http://localhost:8089` 접속
2. 다음 값 입력:
   - **Number of users**: 시뮬레이션할 사용자 수 (예: 20)
   - **Spawn rate**: 초당 생성 속도 (예: 2)
   - **Host**: `http://localhost:8000`
3. **Start swarming** 클릭

## 🔍 주요 매개변수

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-u, --users` | 동시 사용자 수 | `-u 50` |
| `-r, --spawn-rate` | 초당 사용자 생성 수 | `-r 5` |
| `-t, --run-time` | 실행 시간 | `-t 2m` (2분) |
| `--host` | 타겟 URL | `--host=http://localhost:8000` |
| `--headless` | CLI 모드 | `--headless` |
| `--csv` | CSV 결과 저장 | `--csv=results/test` |

## ✅ 사전 확인사항

- [ ] Backend 서버 실행 중 (`docker-compose up` 또는 `./run_app.sh`)
- [ ] 테스트 계정 생성됨 (필요시 `python setup_test_data.py` 실행)
- [ ] `.env` 파일에 올바른 credentials 설정
- [ ] **중요**: HTTP 테스트 시 Backend의 `COOKIE_SECURE=False` 설정 필요

### ⚠️ HTTP 테스트 설정 (필수!)

HTTP로 테스트하는 경우 (`http://localhost:8000`):

```bash
# 1. Backend 설정 파일 수정
# backend/app/settings/.env.dev 열기
# COOKIE_SECURE=False 로 변경

# 2. Backend 재시작
cd /workspaces/FastAPI-MSA-Ready-Template/backend
./run_app.sh
```

**이유**: `COOKIE_SECURE=True`면 쿠키가 HTTPS에서만 전송되어 HTTP 테스트 시 인증 실패가 발생합니다.

## 🎯 테스트 시나리오 예시

```bash
# 1. 가벼운 부하 테스트 (10명의 동시 사용자)
./run_test.sh -u 10 -r 5 -t 1m

# 2. 중간 부하 테스트 (50명의 동시 사용자)
./run_test.sh -u 50 -r 10 -t 3m

# 3. 높은 부하 테스트 (100명의 동시 사용자)
./run_test.sh -u 100 -r 20 -t 5m

# 4. 스파이크 테스트 (급격한 부하 증가)
./run_test.sh -u 200 -r 50 -t 2m

# 5. 인증만 테스트 (LoginOnlyUser 활성화 필요)
# locustfile.py에서 LoginOnlyUser의 weight를 1로 변경 후
./run_test.sh -c LoginOnlyUser -u 30 -r 5 -t 2m
```

## 📝 테스트 동작 방식

- **로그인**: 각 사용자가 시작할 때 1회만 실행
- **부하 테스트**: `/accounts/me` 엔드포인트에 지속적으로 요청
- **대기 시간**: 요청 간 0.1-0.5초 대기 (높은 부하 생성)

## 📈 결과 확인

- **Web UI**: 실시간 그래프와 통계
- **Terminal**: 테스트 완료 후 요약 출력
- **CSV 파일**: `results/` 디렉토리 (--csv 옵션 사용시)

## ❓ 문제 해결

### Backend에 연결할 수 없음
```bash
# Backend 상태 확인
curl http://localhost:8000/health

# Docker 확인
docker-compose ps
```

### 로그인 실패
```bash
# 테스트 계정 생성
python setup_test_data.py

# .env 파일 확인
cat .env
```

더 자세한 내용은 [README.md](README.md)를 참고하세요.
