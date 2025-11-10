import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Main from './pages/Main';
import Login from './pages/account/Login';
import Register from './pages/account/Register';
import FindId from './pages/account/FindId';
import PasswordReset from './pages/account/PasswordReset';
import Profile from './pages/account/Profile';
import './App.css';
import { AuthProvider } from './context/AuthContext';

function App(): React.ReactElement {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Main />} />
          <Route path="/account/login" element={<Login />} />
          <Route path="/account/register" element={<Register />} />
          <Route path="/account/find-id" element={<FindId />} />
          <Route path="/account/password-reset" element={<PasswordReset />} />
          <Route path="/account/profile" element={<Profile />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
