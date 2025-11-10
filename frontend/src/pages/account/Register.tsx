import React, { useState, useEffect, useRef } from 'react';
import './Auth.css';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';

export default function Register() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [email, setEmail] = useState('');
  const [userIdChecked, setUserIdChecked] = useState(false);
  const [userIdAvailable, setUserIdAvailable] = useState<boolean | null>(null);
  const [checkingUserId, setCheckingUserId] = useState(false);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [codeSent, setCodeSent] = useState(false);
  const [code, setCode] = useState('');
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [sendLoading, setSendLoading] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [resendCooldown, setResendCooldown] = useState<number>(0);
  const [emailToken, setEmailToken] = useState<string | null>(null);
  const codeInputRef = useRef<HTMLInputElement | null>(null);

  const validEmail = (v: string) => /\S+@\S+\.\S+/.test(v);
  const passwordsMatch = password === confirm && password.length > 0;
  const canSubmit = userId.trim().length >= 3 && validEmail(email) && passwordsMatch && emailVerified;

  const checkUserId = async () => {
    setError(null);
    const v = userId.trim();
    // 허용되는 문자 검사: 영문 + 숫자만 허용
    const validChars = /^[A-Za-z0-9]+$/.test(v);
    if (!validChars) {
      setError('아이디는 영문과 숫자만 사용할 수 있습니다. (공백/특수문자/한글 불가)');
      return;
    }

    if (v.length < 3) {
      setError('아이디는 3자 이상이어야 합니다.');
      return;
    }
    setCheckingUserId(true);
    setUserIdChecked(false);
    setUserIdAvailable(null);
    try {
      // 아직 API 연동 없음 — 데모용으로 간단히 시뮬레이션
      // 예: 'taken' 또는 'admin'이면 사용불가로 처리
      await new Promise(res => setTimeout(res, 600));
      const unavailable = ['taken', 'admin', 'root'].includes(v.toLowerCase());
      setUserIdAvailable(!unavailable);
      setUserIdChecked(true);
    } catch (_e) {
      setError('아이디 확인 중 오류가 발생했습니다.');
    } finally {
      setCheckingUserId(false);
    }
  };

  // 입력값에 영문+숫자 외 문자가 있는지 검사 (빈 문자열 허용)
  const userIdValidChars = /^[A-Za-z0-9]*$/.test(userId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!canSubmit) {
      setError('입력값을 확인해주세요.');
      return;
    }
    if (!emailToken) {
      setError('이메일 인증 토큰이 없습니다. 이메일 인증을 먼저 완료해주세요.');
      return;
    }
    setLoading(true);
    try {
      // TODO: 실제 백엔드 회원가입 API 호출
      // 요청 페이로드 형식: { token, user_id, username, password, email, phone_number }
      const payload = {
        token: emailToken,
        user_id: userId,
        user_name: userId,
        password,
        email,
        phone_number: '',
      }

      await api.post('/api/v1/accounts', payload);
      // Redirect to login after success
      navigate('/account/login');
    } catch (err) {
      // if backend not available, fall back to fake success for demo
      try {
        await new Promise(res => setTimeout(res, 600));
        navigate('/account/login');
        return;
      } catch (_e) {
        setError('회원가입 중 오류가 발생했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  const sendCode = async () => {
    setError(null);
    if (!validEmail(email)) {
      setError('유효한 이메일을 입력해주세요.');
      return;
    }
    setSendLoading(true);
    try {
      // 요청: 서버에 이메일 인증 토큰 생성 (POST /api/v1/auth/email)
      const res = await api.post('/api/v1/auth/email', { email });
      // 응답에서 token을 꺼내 컴포넌트 state에 저장 (로컬스토리지 대신)
      const token = res?.data?.token;
      if (!token) {
        throw new Error('토큰을 반환하지 않았습니다.');
      }
      setEmailToken(token);
      setCodeSent(true);
      setResendCooldown(60);
      // focus 코드 입력란
      setTimeout(() => codeInputRef.current?.focus(), 80);
    } catch (err: any) {
      // 서버가 없거나 에러인 경우 데모용 폴백 처리
      // (기존 동작과 호환되도록 token은 저장하지 않음)
      setCodeSent(true);
      setResendCooldown(60);
      setTimeout(() => codeInputRef.current?.focus(), 80);
    } finally {
      setSendLoading(false);
    }
  };

  const verifyCode = async () => {
    setError(null);
    if (code.trim().length === 0) {
      setError('인증번호를 입력해주세요.');
      return;
    }
    setVerifyLoading(true);
    try {
      // verification requires token (from previous response) and code
      const token = emailToken;
      if (!token) {
        setError('인증 토큰이 없습니다. 이메일 인증을 다시 요청하세요.');
        setVerifyLoading(false);
        return;
      }

  await api.post('/api/v1/auth/email/verify', { token, code });
  // 성공하면 상태 업데이트 (토큰은 회원가입 시 사용하므로 유지)
      setEmailVerified(true);
      setCodeSent(false);
    } catch (err: any) {
      // 서버에서 401을 반환하면 인증 실패
      const status = err?.response?.status;
      if (status === 401) {
        setError('인증에 실패했습니다. 인증번호를 확인하세요.');
      } else {
        // 데모용 폴백: 코드 '0000' 허용
        if (code === '0000') {
          // 데모 폴백: 인증 성공으로 표시 (토큰이 없는 경우에도 테스트용으로 통과)
          setEmailVerified(true);
          setCodeSent(false);
        } else {
          setError('인증 중 오류가 발생했습니다. 잠시 후 다시 시도하세요.');
        }
      }
    } finally {
      setVerifyLoading(false);
    }
  };

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const id = setInterval(() => setResendCooldown(c => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [resendCooldown]);

  return (
    <div className="auth-container">
      <h2>회원가입</h2>
      <p className="auth-sub">간단한 정보로 안전하게 계정을 만들어보세요</p>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="input-group">
          <label>아이디</label>
          <div className="input-row">
            <div className="input-wrap">
              <input value={userId} onChange={e => { setUserId(e.target.value); setUserIdChecked(false); setUserIdAvailable(null); }} placeholder="3자 이상" />
            </div>
            <button
              type="button"
              className="small-btn"
              onClick={checkUserId}
              disabled={checkingUserId || userId.trim().length < 3 || !userIdValidChars}
            >
              {checkingUserId ? '확인중...' : (userIdAvailable === true ? '사용가능' : (userIdAvailable === false ? '사용불가' : '중복확인'))}
            </button>
          </div>
          {/* 영어(알파벳)과 숫자만 허용한다는 안내 */}
          {userId.length > 0 && !userIdValidChars && (
            <small style={{ color: 'crimson' }}>아이디는 영문(대/소문자)과 숫자만 사용할 수 있습니다. 다른 언어(한글 등) 또는 특수문자는 사용할 수 없습니다.</small>
          )}
          {userIdChecked && userIdAvailable === true && (
            <small style={{ color: 'green' }}>사용 가능한 아이디입니다.</small>
          )}
          {userIdChecked && userIdAvailable === false && (
            <small style={{ color: 'crimson' }}>이미 사용 중인 아이디입니다.</small>
          )}
        </div>

        <div className="input-group">
          <label>이메일</label>
          <div className="input-row">
            <div className="input-wrap">
              <input
                type="email"
                value={email}
                onChange={e => { setEmail(e.target.value); setEmailVerified(false); setCodeSent(false); }}
                placeholder="example@domain.com"
              />
            </div>
            <button
              type="button"
              className="small-btn"
              onClick={sendCode}
              disabled={resendCooldown > 0 || emailVerified || sendLoading}
            >
              {sendLoading ? '전송중...' : (resendCooldown > 0 ? `재전송(${resendCooldown}s)` : emailVerified ? '인증완료' : '인증요청')}
            </button>
          </div>
        </div>

        {codeSent && !emailVerified && (
          <div className="input-group">
            <label>이메일 인증번호</label>
            <div className="input-row">
              <div className="input-wrap">
                <input ref={codeInputRef} value={code} onChange={e => setCode(e.target.value)} placeholder="인증번호를 입력하세요" />
              </div>
              <button type="button" className="small-btn" onClick={verifyCode} disabled={verifyLoading}>{verifyLoading ? '확인중...' : '확인'}</button>
            </div>
          </div>
        )}

        {emailVerified && (
          <div style={{ display:'flex', gap:8, alignItems:'center' }} aria-live="polite">
            <div className="verified-badge">인증 완료</div>
          </div>
        )}

        <div className="input-group">
          <label>비밀번호</label>
          <div className="input-row">
            <div className="input-wrap">
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호" />
            </div>
          </div>
          <small className="auth-sub pw-hint">영문 대문자, 숫자, 특수문자 포함 8~16자 권장</small>
        </div>

        <div className="input-group">
          <label>비밀번호 확인</label>
          <div className="input-row">
            <div className="input-wrap">
              <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="비밀번호 확인" />
            </div>
          </div>
        </div>

        {error && <div style={{ color: 'crimson', fontSize: '0.95rem' }}>{error}</div>}

        <button type="submit" className="primary" disabled={loading || !canSubmit}>{loading ? '등록 중...' : '회원가입'}</button>

        <div className="auth-links">
          <button type="button" className="auth-link" onClick={() => navigate('/account/login')}>로그인으로 돌아가기</button>
        </div>
      </form>
    </div>
  );
}

