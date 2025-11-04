import React, { useEffect, useRef, useState } from 'react';
import './Auth.css';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

declare global {
  interface Window {
    google?: any;
  }
}

const GOOGLE_CLIENT_ID = '1008734949255-c3efrof5a6tri4kh08tens0ckssfohqj.apps.googleusercontent.com';

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
  const googleClient = useRef<any>(null);
  const [isGoogleReady, setIsGoogleReady] = useState(false);

  const onSocial = (provider: string) => {
    if (provider === 'google') {
      if (!googleClient.current) {
        console.warn('Google OAuth 초기화 중입니다. 잠시 후 다시 시도해주세요.');
        return;
      }

      try {
        googleClient.current.requestAccessToken({ prompt: isGoogleReady ? undefined : 'consent' });
      } catch (err) {
        console.error('Google OAuth 요청 중 오류가 발생했습니다.', err);
      }
      return;
    }

    // TODO: 연결된 OAuth 엔드포인트로 이동시키거나 팝업 열기
    // 예: window.location.href = `${process.env.REACT_APP_API_BASE_URL}/auth/oauth/${provider}`
    console.log(`social login: ${provider}`);
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeGoogleOAuth = () => {
      if (!window.google?.accounts?.oauth2) {
        console.warn('Google OAuth 클라이언트를 찾을 수 없습니다.');
        return;
      }

      googleClient.current = window.google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'openid profile email',
        prompt: 'consent',
        callback: (tokenResponse: { access_token: string; expires_in: number; token_type: string; scope: string }) => {
          console.log('Google OAuth Token Response:', tokenResponse);
        },
        error_callback: (err: unknown) => {
          console.error('Google OAuth 에러:', err);
        }
      });

      setIsGoogleReady(true);
    };

    if (window.google?.accounts?.oauth2) {
      initializeGoogleOAuth();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogleOAuth;
    script.onerror = () => {
      console.error('Google OAuth 스크립트 로드에 실패했습니다.');
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, []);

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
            <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="아이디를 입력하세요" />
          </div>
        </div>

        <div className="input-group">
        <label>비밀번호</label>
          <div className="input-row">
            <div className="input-wrap">
              <input
                type="password"
                value={password}
                onChange={e=>setPassword(e.target.value)}
                placeholder="비밀번호"
              />
            </div>
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
          <span className="label">Google로 로그인</span>
        </button>
      </div>
    </div>
  );
}
