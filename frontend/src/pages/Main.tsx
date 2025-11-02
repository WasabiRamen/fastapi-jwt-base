import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Main.css';
import logo from '../logo.svg';
import api from '../lib/api';
import LaunchClock from '../components/LaunchClock';

export default function Main() {
  // Restore header authentication state so header remains functional while we show
  // the launch UI below.
  const getInitial = () => {
    try {
      const v = sessionStorage.getItem('isLoggedIn');
      if (v === 'true') return true;
      if (v === 'false') return false;
    } catch (e) {
      // sessionStorage may be unavailable; fall back to null
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
        const status = err?.response?.status;
        if (status === 401) {
          try {
            await api.post('/api/v1/auth/token/refresh');
            const retry = await api.get('/api/v1/accounts/me');
            if (mounted && retry.status === 200) {
              setIsLoggedIn(true);
              try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
              return;
            }
          } catch (_refreshErr) {
            // fall through
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
    try { await api.delete('/api/v1/auth/logout'); } catch (e) {}
    setIsLoggedIn(false);
    try { sessionStorage.setItem('isLoggedIn', 'false'); } catch {}
    navigate('/');
  };

  const [showLogoutModal, setShowLogoutModal] = useState<boolean>(false);
  const confirmLogout = async () => {
    setShowLogoutModal(false);
    await handleLogout();
  };

  

  return (
    <>
      <header className="main-gnb">
        <div className="main-left">
          <img src={logo} alt="HiLi" className="main-logo" />
        </div>
        <nav className="main-right">
          {checking && isLoggedIn === null ? (
            <span className="login-btn">...</span>
          ) : isLoggedIn ? (
            <>
              <button type="button" className="login-btn" onClick={() => setShowLogoutModal(true)}>로그아웃</button>
              {showLogoutModal && (
                <div className="modal-overlay" role="dialog" aria-modal="true">
                  <div className="modal-box">
                    <h3>로그아웃 확인</h3>
                    <p>진짜 로그아웃 하시겠습니까?</p>
                    <div className="modal-actions">
                      <button className="btn-cancel" onClick={() => setShowLogoutModal(false)}>취소</button>
                      <button className="btn-confirm" onClick={confirmLogout}>로그아웃</button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Link to="/account/login" className="login-btn">로그인</Link>
          )}
        </nav>
      </header>

      <LaunchClock />
    </>
  );
}
