import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Main from './pages/Main';
import Login from './pages/account/Login';
import Register from './pages/account/Register';
import FindId from './pages/account/FindId';
import PasswordReset from './pages/account/PasswordReset';
import './App.css';

function App(): React.ReactElement {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/account/login" element={<Login />} />
        <Route path="/account/register" element={<Register />} />
        <Route path="/account/find-id" element={<FindId />} />
        <Route path="/account/password-reset" element={<PasswordReset />} />
      </Routes>
    </Router>
  );
}

export default App;
