import React from 'react';
import './Auth.css';

export default function Register(){
  return (
    <div className="auth-container">
      <h2>회원가입</h2>
      <form className="auth-form">
        <label>아이디</label>
        <input />
        <label>비밀번호</label>
        <input type="password" />
        <label>비밀번호 확인</label>
        <input type="password" />
        <button type="submit">회원가입</button>
      </form>
    </div>
  );
}
