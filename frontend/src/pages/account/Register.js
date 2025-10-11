import './Auth.css';

export default function Register() {
  return (
    <div className="auth-container">
      <h2>회원가입</h2>
      <form className="auth-form">
        <label htmlFor="username">아이디</label>
        <input type="text" id="username" name="username" placeholder="아이디를 입력하세요" required />
        <label htmlFor="password">비밀번호</label>
        <input type="password" id="password" name="password" placeholder="비밀번호를 입력하세요" required />
        <label htmlFor="confirm">비밀번호 확인</label>
        <input type="password" id="confirm" name="confirm" placeholder="비밀번호를 다시 입력하세요" required />
        <button type="submit">회원가입</button>
      </form>
      <div className="auth-link">
        <a href="/account/login">로그인</a>
      </div>
    </div>
  );
}
