import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Main.css';
import logo from '../logo.svg';
import defaultUser from '../default_user.svg';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
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
  const auth = useAuth();

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        await auth.fetchCurrentUser();
        if (mounted) {
          setIsLoggedIn(true);
          try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
          return;
        }
      } catch (err: any) {
        const status = (err as any)?.response?.status;
        if (status === 401) {
          try {
            await api.post('/api/v1/auth/token/refresh');
            await auth.fetchCurrentUser();
            if (mounted) {
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

  const [showUserMenu, setShowUserMenu] = useState<boolean>(false);
  const avatarRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!showUserMenu) return;
      const target = e.target as Node;
      if (avatarRef.current && !avatarRef.current.contains(target)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [showUserMenu]);

  

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
              <div className="avatar-wrap" ref={avatarRef}>
                <img src={defaultUser} alt="user" className="user-avatar" onClick={() => setShowUserMenu(s => !s)} />
                {showUserMenu && (
                  <div className="user-menu" role="menu" aria-label="사용자 메뉴">
                    <button className="user-menu-item" role="menuitem" onClick={() => { setShowUserMenu(false); navigate('/account/profile'); }}>
                      내 프로필
                    </button>
                    <button className="user-menu-item" role="menuitem" onClick={() => { setShowUserMenu(false); setShowLogoutModal(true); }}>
                      로그아웃
                    </button>
                  </div>
                )}
              </div>
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
