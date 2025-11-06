import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

declare global {
  interface Window {
    google?: any;
  }
}

const GOOGLE_CLIENT_ID = '1008734949255-c3efrof5a6tri4kh08tens0ckssfohqj.apps.googleusercontent.com';

interface UseGoogleLoginReturn {
  isGoogleReady: boolean;
  handleGoogleLogin: () => void;
  googleLoading: boolean;
  googleError: string | null;
}

export const useGoogleLogin = (): UseGoogleLoginReturn => {
  const googleClient = useRef<any>(null);
  const [isGoogleReady, setIsGoogleReady] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeGoogleOAuth = () => {
      if (!window.google?.accounts?.oauth2) {
        console.warn('Google OAuth 클라이언트를 찾을 수 없습니다.');
        return;
      }

      // 팝업 기반 Google OAuth 초기화 (redirect_uri 포함)
      googleClient.current = window.google.accounts.oauth2.initCodeClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'openid profile email',
        ux_mode: 'popup',
        redirect_uri: 'postmessage',
        callback: async (codeResponse: { code: string }) => {
          console.log('Google OAuth Code Response (popup):', codeResponse);
          
          if (!codeResponse?.code) {
            console.error('No authorization code received from Google popup.');
            setGoogleError('Google 인증 코드를 받지 못했습니다.');
            return;
          }

          // 백엔드로 인증 코드 전송
          try {
            setGoogleLoading(true);
            setGoogleError(null);

            const resp = await api.post('/api/v1/auth/google/login', { 
              code: codeResponse.code,
            });

            // 로그인 성공 처리
            try { 
              sessionStorage.setItem('isLoggedIn', 'true'); 
            } catch {}
            
            navigate('/');
            return resp;
          } catch (err: any) {
            console.error('Failed to send Google code to backend:', err?.response || err);
            const errorMessage = err?.response?.data?.detail || '구글 로그인 처리 중 오류가 발생했습니다.';
            setGoogleError(errorMessage);
          } finally {
            setGoogleLoading(false);
          }
        },
        error_callback: (err: unknown) => {
          console.error('Google OAuth 에러:', err);
          setGoogleError('Google OAuth 인증 중 오류가 발생했습니다.');
          setGoogleLoading(false);
        }
      });

      setIsGoogleReady(true);
    };

    // Google OAuth 스크립트가 이미 로드되어 있는 경우
    if (window.google?.accounts?.oauth2) {
      initializeGoogleOAuth();
      return;
    }

    // Google OAuth 스크립트 동적 로드
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogleOAuth;
    script.onerror = () => {
      console.error('Google OAuth 스크립트 로드에 실패했습니다.');
      setGoogleError('Google OAuth 스크립트를 로드할 수 없습니다.');
    };
    document.head.appendChild(script);

    // 클린업
    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [navigate]);

  const handleGoogleLogin = () => {
    setGoogleError(null);
    
    if (!googleClient.current) {
      console.warn('Google OAuth 초기화 중입니다. 잠시 후 다시 시도해주세요.');
      setGoogleError('Google OAuth 초기화 중입니다. 잠시 후 다시 시도해주세요.');
      return;
    }

    try {
      // 팝업으로 Google 인증 시작
      googleClient.current.requestCode({ 
        prompt: isGoogleReady ? undefined : 'consent' 
      });
    } catch (err) {
      console.error('Google OAuth 요청 중 오류가 발생했습니다.', err);
      setGoogleError('Google OAuth 요청 중 오류가 발생했습니다.');
    }
  };

  return {
    isGoogleReady,
    handleGoogleLogin,
    googleLoading,
    googleError
  };
};
