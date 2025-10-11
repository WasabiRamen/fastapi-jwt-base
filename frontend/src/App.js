
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/account/Login';
import Register from './pages/account/Register';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/account/login" element={<Login />} />
        <Route path="/account/register" element={<Register />} />
        {/* 필요시 메인/기타 라우트 추가 */}
      </Routes>
    </Router>
  );
}

export default App;
