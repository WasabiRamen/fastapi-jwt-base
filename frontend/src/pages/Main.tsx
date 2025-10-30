import React from 'react';
import { Link } from 'react-router-dom';
import './Main.css';

export default function Main() {
  return (
    <header className="main-gnb">
      <div className="main-left">HiLi</div>
      <nav className="main-right">
        <Link to="/account/login" className="login-btn">로그인</Link>
      </nav>
    </header>
  );
}
