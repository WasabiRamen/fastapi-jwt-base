import React, { useState } from 'react';
import './Auth.css';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validEmail = (v: string) => /\S+@\S+\.\S+/.test(v);
  const passwordsMatch = password === confirm && password.length > 0;
  const canSubmit = username.trim().length >= 3 && validEmail(email) && passwordsMatch;

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
      // 예: await api.post('/auth/register', { username, email, password })
      await new Promise(res => setTimeout(res, 600)); // fake delay
      // Redirect to login after success
      navigate('/account/login');
    } catch (err) {
      setError('회원가입 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>회원가입</h2>
      <p className="auth-sub">간단한 정보로 안전하게 계정을 만들어보세요</p>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="input-group">
          <label>아이디</label>
          <div className="input-wrap">
            <span className="input-icon">@</span>
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="3자 이상" />
          </div>
        </div>

        <div className="input-group">
          <label>이메일</label>
          <div className="input-wrap">
            <span className="input-icon">✉️</span>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@domain.com" />
          </div>
        </div>

        <div className="input-group">
          <label>비밀번호</label>
          <div className="input-wrap">
            <span className="input-icon">🔒</span>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호" />
          </div>
          <small className="auth-sub">영문 대문자, 숫자, 특수문자 포함 8~16자 권장</small>
        </div>

        <div className="input-group">
          <label>비밀번호 확인</label>
          <div className="input-wrap">
            <span className="input-icon">🔒</span>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="비밀번호 확인" />
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

