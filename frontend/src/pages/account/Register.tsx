import React, { useState, useEffect, useRef } from 'react';
import './Auth.css';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
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
  const codeInputRef = useRef<HTMLInputElement | null>(null);

  const validEmail = (v: string) => /\S+@\S+\.\S+/.test(v);
  const passwordsMatch = password === confirm && password.length > 0;
  const canSubmit = username.trim().length >= 3 && validEmail(email) && passwordsMatch && emailVerified;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!canSubmit) {
      setError('입력값을 확인해주세요.');
      return;
    }
    setLoading(true);
    try {
      // TODO: 실제 백엔드 회원가입 API 호출
      // 예: await api.post('/api/v1/auth/register', { username, email, password })
      await api.post('/api/v1/auth/register', { username, email, password });
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
      // 요청: 서버에 이메일 인증번호 전송
      await api.post('/api/v1/auth/email/send-code', { email });
      setCodeSent(true);
      setResendCooldown(60);
      setTimeout(() => codeInputRef.current?.focus(), 80);
    } catch (err) {
      // fallback fake (demo)
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
      await api.post('/api/v1/auth/email/verify', { email, code });
      setEmailVerified(true);
      setCodeSent(false);
    } catch (err) {
      // fallback: accept any code '0000' in demo
      if (code === '0000') {
        setEmailVerified(true);
        setCodeSent(false);
      } else {
        setError('인증에 실패했습니다. 인증번호를 확인하세요.');
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
              <input value={username} onChange={e => setUsername(e.target.value)} placeholder="3자 이상" />
            </div>
          </div>
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

