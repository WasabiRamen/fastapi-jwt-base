import React, { useEffect, useRef, useState } from 'react';
import './Auth.css';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import defaultUser from '../../default_user.svg';
import { useGoogleLink } from '../../hooks/useGoogleLink';

export default function Profile(){
  const auth = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<{ username: string; email: string; avatar_url?: string } | null>(null);

  // avatar upload preview
  const [preview, setPreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  // google link hook
  const { isGoogleReady, handleGoogleLink, googleLoading, googleError, googleLinked, setGoogleLinked } = useGoogleLink();

  useEffect(() => {
    let mounted = true;
    const loadUser = async () => {
      try {
        const data = await auth.fetchCurrentUser();
        if (!mounted) return;
        setUser(data || { username: '', email: '' });
        // rudimentary: if the response contains google_linked flag
        if (data?.google_linked) setGoogleLinked(true);
      } catch (err:any) {
        setError('사용자 정보를 불러오는 중 오류가 발생했습니다.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    loadUser();
    return () => { mounted = false };
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const uploadAvatar = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) return setError('업로드할 파일을 선택해주세요.');
    const fd = new FormData();
    fd.append('avatar', f);
    try {
      setLoading(true);
      await api.post('/api/v1/accounts/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      // refresh user via centralized fetch (force)
      const data = await auth.fetchCurrentUser(true);
      setUser(data);
      setPreview(null);
    } catch (err:any) {
      setError('아바타 업로드에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const unlinkGoogle = async () => {
    try {
      await api.post('/api/v1/auth/google/unlink');
      setGoogleLinked(false);
    } catch (err) {
      setError('구글 연동 해제 중 오류가 발생했습니다.');
    }
  };

  if (loading) return <div className="auth-container"><p>로딩중...</p></div>;

  return (
    <div className="auth-container">
      <h2>내 프로필</h2>
      {error && <div style={{ color: 'crimson' }}>{error}</div>}

      <div style={{ display: 'grid', gap: 12, width: '100%' }}>
        <div>
          <label style={{ display:'block', marginBottom:8 }}>프로필 사진 변경</label>
          <div style={{ display:'flex', gap:12, alignItems:'center' }}>
            <div style={{ width:80, height:80, borderRadius:999, overflow:'hidden', border:'1px solid #e6eef2' }}>
              <img src={preview || user?.avatar_url || defaultUser} alt="avatar" style={{ width:'100%', height:'100%', objectFit:'cover' }} />
            </div>
            <div style={{ display:'flex', gap:8 }}>
              <input type="file" accept="image/*" ref={fileRef} onChange={onFileChange} />
              <button className="small-btn" type="button" onClick={uploadAvatar}>업로드</button>
            </div>
          </div>
        </div>

        <div>
          <label>아이디</label>
          <div className="input-wrap" style={{ marginTop:8 }}>
            <input value={user?.username || ''} disabled />
          </div>
        </div>

        <div>
          <label>Email</label>
          <div className="input-wrap" style={{ marginTop:8 }}>
            <input value={user?.email || ''} disabled />
          </div>
        </div>

        <div>
          <label>구글 ID 연동하기</label>
          <div style={{ marginTop:8, display:'flex', gap:8, alignItems:'center' }}>
            {googleLinked ? (
              <>
                <div style={{ color:'#0b6356', fontWeight:700 }}>연결됨</div>
                <button className="small-btn" onClick={unlinkGoogle}>연결해제</button>
              </>
            ) : (
              <button 
                className="small-btn" 
                onClick={handleGoogleLink}
                disabled={!isGoogleReady || googleLoading}
              >
                {googleLoading ? '연동 중...' : '구글 연동'}
              </button>
            )}
          </div>
          {googleError && <div style={{ color: 'crimson', marginTop: 4, fontSize: '0.9em' }}>{googleError}</div>}
        </div>
      </div>
    </div>
  );
}
