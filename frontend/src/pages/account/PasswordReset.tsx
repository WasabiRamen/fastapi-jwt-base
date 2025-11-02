import React, { useState } from 'react';
import './Auth.css';

export default function PasswordReset() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<string | null>(null);

  const handleRequest = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: call backend endpoint to start password reset flow
    // 예시: await api.post('/auth/password-reset', { email })
    setStatus('비밀번호 재설정 링크가 이메일로 전송되었습니다. (더미 메시지)');
  };

  return (
    <div className="auth-container">
      <h2>비밀번호 찾기 / 재설정</h2>
      <p className="auth-sub">계정과 연결된 이메일을 입력하면 재설정 링크를 보냅니다.</p>

      <form className="auth-form" onSubmit={handleRequest}>
        <label>이메일</label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@domain.com" />
        <button type="submit" className="primary">재설정 링크 전송</button>
      </form>

      {status && <div className="auth-result">{status}</div>}
    </div>
  );
}
