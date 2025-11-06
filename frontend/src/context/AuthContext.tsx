import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface AuthState {
  isLoggedIn: boolean;
  loading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isLoggedIn: sessionStorage.getItem('isLoggedIn') === 'true',
    loading: false,
    error: null,
  });
  const navigate = useNavigate();

  const login = async (username: string, password: string): Promise<void> => {
    setAuthState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);
      
      await api.post<LoginResponse>('/api/v1/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      // 로그인 성공
      try { 
        sessionStorage.setItem('isLoggedIn', 'true'); 
      } catch {}
      
      setAuthState(prev => ({ 
        ...prev, 
        isLoggedIn: true, 
        loading: false, 
        error: null 
      }));
      
      navigate('/');
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || '로그인에 실패했습니다.';
      setAuthState(prev => ({ 
        ...prev, 
        loading: false, 
        error: errorMessage 
      }));
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    try {
      sessionStorage.removeItem('isLoggedIn');
    } catch {}
    
    setAuthState({
      isLoggedIn: false,
      loading: false,
      error: null,
    });
    
    navigate('/account/login');
  };

  const setError = (error: string | null) => {
    setAuthState(prev => ({ ...prev, error }));
  };

  const setLoading = (loading: boolean) => {
    setAuthState(prev => ({ ...prev, loading }));
  };

  const clearError = () => {
    setAuthState(prev => ({ ...prev, error: null }));
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    logout,
    setError,
    setLoading,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
