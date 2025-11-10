import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

// module-level in-flight promise to dedupe concurrent requests for current user
let currentUserInFlight: Promise<any> | null = null;

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
  // current user and helpers
  currentUser: any | null;
  fetchCurrentUser: (force?: boolean) => Promise<any>;
  invalidateCurrentUser: () => void;
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
  const [currentUser, setCurrentUser] = useState<any | null>(null);
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
      // after login, populate current user (best-effort)
      try { await fetchCurrentUser(true); } catch (_) {}
      
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
    setCurrentUser(null);
    setAuthState({
      isLoggedIn: false,
      loading: false,
      error: null,
    });
    
    navigate('/account/login');
  };

  // fetchCurrentUser: cached + in-flight dedupe
  const fetchCurrentUser = async (force = false) => {
    if (!force && currentUser) return currentUser;
    if (currentUserInFlight) return currentUserInFlight;
    currentUserInFlight = api.get('/api/v1/accounts/me')
      .then(r => {
        setCurrentUser(r.data);
        try { sessionStorage.setItem('isLoggedIn', 'true'); } catch {}
        setAuthState(prev => ({ ...prev, isLoggedIn: true }));
        currentUserInFlight = null;
        return r.data;
      })
      .catch(err => {
        currentUserInFlight = null;
        // if unauthorized, mark logged out
        const status = (err as any)?.response?.status;
        if (status === 401) {
          try { sessionStorage.setItem('isLoggedIn', 'false'); } catch {}
          setAuthState(prev => ({ ...prev, isLoggedIn: false }));
        }
        throw err;
      });
    return currentUserInFlight;
  };

  const invalidateCurrentUser = () => setCurrentUser(null);

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
    currentUser,
    login,
    logout,
    setError,
    setLoading,
    clearError,
    fetchCurrentUser,
    invalidateCurrentUser,
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
