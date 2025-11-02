import React, { useState } from 'react';
import './Auth.css';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Send credentials as application/x-www-form-urlencoded because the backend
// uses OAuth2PasswordRequestForm (FastAPI). Axios instance (`api`) has
// withCredentials: true so cookies set by the server will be stored.
const handleLogin = async (username: string, password: string): Promise<LoginResponse> => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  // OAuth2PasswordRequestForm may expect grant_type, scope, etc. but username/password are sufficient here.
  const response = await api.post<LoginResponse>('/api/v1/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return response.data;
}


export default function Login(){
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const onSocial = (provider: string) => {
    // TODO: 연결된 OAuth 엔드포인트로 이동시키거나 팝업 열기
    // 예: window.location.href = `${process.env.REACT_APP_API_BASE_URL}/auth/oauth/${provider}`
    console.log(`social login: ${provider}`);
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await handleLogin(username, password);
      // login successful; server likely set HttpOnly cookies
      // persist a lightweight hint to sessionStorage so the UI can show
      // the previous auth state immediately while the client re-validates.
      try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>로그인</h2>
      <p className="auth-sub">계정으로 안전하게 로그인하세요</p>

      <form className="auth-form" onSubmit={onSubmit}>
        <div className="input-group">
          <label>아이디</label>
          <div className="input-wrap">
            <span className="input-icon">@</span>
            <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="아이디를 입력하세요" />
          </div>
        </div>

        <div className="input-group">
          <label>비밀번호</label>
          <div className="input-wrap">
            <span className="input-icon">🔒</span>
            <input 
            type="password" 
            value={password} 
            onChange={e=>setPassword(e.target.value)} 
            placeholder="비밀번호" />
          </div>
        </div>

  <button type="submit" className="primary" disabled={loading}>{loading ? '로딩...' : '로그인'}</button>
  {error && <div style={{ color: 'crimson', fontSize: '0.95rem' }}>{error}</div>}
        <div className="auth-links">
          <button type="button" className="auth-link" onClick={() => navigate('/account/password-reset')}>비밀번호 찾기</button>
          <button type="button" className="auth-link" onClick={() => navigate('/account/find-id')}>아이디 찾기</button>
          <button type="button" className="auth-link" onClick={() => navigate('/account/register')}>회원가입</button>
        </div>
      </form>

      <div className="divider"><span>또는</span></div>

      <div className="social-login">
        <button type="button" className="social-btn google" aria-label="구글 로그인" onClick={()=>onSocial('google')}>
          <span className="icon">G</span>
          <span className="label">구글로 계속하기</span>
        </button>
        <button type="button" className="social-btn kakao" aria-label="카카오 로그인" onClick={()=>onSocial('kakao')}>
          <span className="icon">K</span>
          <span className="label">카카오로 계속하기</span>
        </button>
        <button type="button" className="social-btn naver" aria-label="네이버 로그인" onClick={()=>onSocial('naver')}>
          <span className="icon">N</span>
          <span className="label">네이버로 계속하기</span>
        </button>
      </div>
    </div>
  );
}
