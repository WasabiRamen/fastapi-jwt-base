import React, { useState } from 'react';
import './Auth.css';

export default function FindId() {
  const [email, setEmail] = useState('');
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: call backend endpoint to find ID by email
    // 예시: await api.post('/auth/find-id', { email })
    setResult('아이디가 등록된 이메일로 전송되었습니다. (더미 메시지)');
  };

  return (
    <div className="auth-container">
      <h2>아이디 찾기</h2>
      <p className="auth-sub">회원가입 시 사용한 이메일을 입력하세요</p>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>이메일</label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@domain.com" />
        <button type="submit" className="primary">아이디 찾기</button>
      </form>

      {result && <div className="auth-result">{result}</div>}
    </div>
  );
}
