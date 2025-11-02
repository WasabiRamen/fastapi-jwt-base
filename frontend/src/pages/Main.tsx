import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Main.css';
import logo from '../logo.svg';
import api from '../lib/api';

export default function Main() {
  // Initialize from sessionStorage so we can show the previous state
  // while the app re-validates the session with the server.
  const getInitial = () => {
    try {
      const v = sessionStorage.getItem('isLoggedIn');
      if (v === 'true') return true;
      if (v === 'false') return false;
    } catch (e) {
      // sessionStorage may be unavailable in some environments; fall back to null
    }
    return null;
  };

  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(getInitial);
  const [checking, setChecking] = useState<boolean>(true);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const resp = await api.get('/api/v1/accounts/me');
        if (mounted && resp.status === 200) {
          setIsLoggedIn(true);
          try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
          return;
        }
      } catch (err: any) {
        // If 401, try refresh flow then re-check
        const status = err?.response?.status;
        if (status === 401) {
          try {
            // attempt token refresh (server reads refresh token from cookie)
            await api.post('/api/v1/auth/token/refresh');
            // retry checking account
            const retry = await api.get('/api/v1/accounts/me');
            if (mounted && retry.status === 200) {
              setIsLoggedIn(true);
              try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
              return;
            }
          } catch (_refreshErr) {
            // refresh failed, fall through to logout
          }
        }
        if (mounted) {
          setIsLoggedIn(false);
          try { sessionStorage.setItem('isLoggedIn', 'false'); } catch {}
        }
      } finally {
        if (mounted) setChecking(false);
      }
    };
    check();
    return () => { mounted = false; };
  }, []);

  const handleLogout = async () => {
    try {
      await api.delete('/api/v1/auth/logout');
    } catch (err) {
      // ignore errors; ensure UI updates
    }
    setIsLoggedIn(false);
    try { sessionStorage.setItem('isLoggedIn', 'false'); } catch {}
    navigate('/');
  };

  return (
    <>
      <header className="main-gnb">
        <div className="main-left">
          <img src={logo} alt="HiLi" className="main-logo" />
        </div>
        <nav className="main-right">
          {checking && isLoggedIn === null ? (
            // No previous state found and we're still validating -> show placeholder
            <span className="login-btn">...</span>
          ) : isLoggedIn ? (
            <button type="button" className="login-btn" onClick={handleLogout}>로그아웃</button>
          ) : (
            <Link to="/account/login" className="login-btn">로그인</Link>
          )}
        </nav>
      </header>

      <main className="main-content">
        <section className="hero">
          <h1>환영합니다 — HiLi 샘플 애플리케이션</h1>
          <p className="lead">빠르고 안전한 인증 템플릿을 학습하고 테스트할 수 있는 데모 페이지입니다.</p>
          <div className="hero-cta">
            {isLoggedIn ? (
              <button className="primary" onClick={() => window.location.reload()}>내 계정 보기</button>
            ) : (
              <Link to="/account/register" className="primary">회원가입 시작</Link>
            )}
            <Link to="/account/login" className="secondary">로그인</Link>
          </div>
        </section>

        <section className="features">
          <article className="feature-card">
            <h3>보안 중심 설계</h3>
            <p>HttpOnly 쿠키, SameSite, Secure 설정 예제를 통해 안전한 토큰 관리를 연습하세요.</p>
          </article>
          <article className="feature-card">
            <h3>OAuth2 흐름</h3>
            <p>OAuth2 Password / Refresh 토큰 흐름을 간단히 확인할 수 있습니다.</p>
          </article>
          <article className="feature-card">
            <h3>간단한 UI</h3>
            <p>React 기반의 최소한의 계정 페이지가 준비되어 있습니다. 직접 수정해보세요.</p>
          </article>
        </section>

        <footer className="site-footer">
          <p>© {new Date().getFullYear()} HiLi — Demo</p>
        </footer>
      </main>
    </>
  );
}
