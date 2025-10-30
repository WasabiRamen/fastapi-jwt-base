import React, { useState } from 'react';
import './Auth.css';

export default function Login(){
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="auth-container">
      <h2>로그인</h2>
      <form className="auth-form">
        <label>아이디</label>
        <input value={username} onChange={e=>setUsername(e.target.value)} />
        <label>비밀번호</label>
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit">로그인</button>
      </form>
    </div>
  );
}
