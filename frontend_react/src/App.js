import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const AUTH_URL = "https://auth-service-1044319150113.europe-west1.run.app";
const POST_URL = "https://post-service-1044319150113.europe-west1.run.app";

function decodeJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '');
  const [currentUser, setCurrentUser] = useState(() => {
    const t = localStorage.getItem('token');
    return t ? decodeJwt(t)?.username : null;
  });
  const [currentUserId, setCurrentUserId] = useState(() => {
    const t = localStorage.getItem('token');
    return t ? decodeJwt(t)?.user_id : null;
  });

  const [authMode, setAuthMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const [postContent, setPostContent] = useState('');
  const [posts, setPosts] = useState([]);
  const [editingPostId, setEditingPostId] = useState(null);
  const [editContent, setEditContent] = useState('');

  const [message, setMessage] = useState({ text: '', type: '' });
  const [loading, setLoading] = useState(false);

  const showMessage = (text, type) => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 4000);
  };

  const fetchPosts = useCallback(async () => {
    try {
      const res = await fetch(`${POST_URL}/posts?limit=20&offset=0`);
      if (!res.ok) throw new Error('fetch failed');
      setPosts(await res.json());
    } catch {
      showMessage('Błąd podczas pobierania postów', 'error');
    }
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${AUTH_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) {
        showMessage('Rejestracja zakończona sukcesem! Możesz się zalogować.', 'success');
        setAuthMode('login');
        setPassword('');
      } else {
        showMessage(data.detail || 'Rejestracja nieudana', 'error');
      }
    } catch {
      showMessage('Błąd połączenia', 'error');
    }
    setLoading(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${AUTH_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) {
        const t = data.access_token;
        const payload = decodeJwt(t);
        setToken(t);
        setCurrentUser(payload?.username);
        setCurrentUserId(payload?.user_id);
        localStorage.setItem('token', t);
        showMessage('Zalogowano pomyślnie!', 'success');
        setUsername('');
        setPassword('');
      } else {
        showMessage(data.detail || 'Logowanie nieudane', 'error');
      }
    } catch {
      showMessage('Błąd połączenia', 'error');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setToken('');
    setCurrentUser(null);
    setCurrentUserId(null);
    localStorage.removeItem('token');
    showMessage('Wylogowano', 'success');
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!postContent.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${POST_URL}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content: postContent }),
      });
      const data = await res.json();
      if (res.ok) {
        showMessage('Post opublikowany!', 'success');
        setPostContent('');
        fetchPosts();
      } else {
        showMessage(data.detail || 'Nie udało się utworzyć postu', 'error');
      }
    } catch {
      showMessage('Błąd połączenia', 'error');
    }
    setLoading(false);
  };

  const handleDeletePost = async (postId) => {
    try {
      const res = await fetch(`${POST_URL}/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        showMessage('Post usunięty', 'success');
        fetchPosts();
      } else {
        const data = await res.json();
        showMessage(data.detail || 'Nie udało się usunąć postu', 'error');
      }
    } catch {
      showMessage('Błąd połączenia', 'error');
    }
  };

  const startEdit = (post) => {
    setEditingPostId(post.id);
    setEditContent(post.content);
  };

  const handleUpdatePost = async (postId) => {
    try {
      const res = await fetch(`${POST_URL}/posts/${postId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content: editContent }),
      });
      if (res.ok) {
        showMessage('Post zaktualizowany!', 'success');
        setEditingPostId(null);
        fetchPosts();
      } else {
        const data = await res.json();
        showMessage(data.detail || 'Nie udało się zaktualizować postu', 'error');
      }
    } catch {
      showMessage('Błąd połączenia', 'error');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">mini social media!</h1>
        {currentUser && (
          <div className="user-bar">
            <span className="user-greeting">Zalogowany jako <strong>{currentUser}</strong></span>
            <button className="btn btn-outline" onClick={handleLogout}>Wyloguj</button>
          </div>
        )}
      </header>

      {message.text && (
        <div className={`message message-${message.type}`}>{message.text}</div>
      )}

      <main className="app-main">
        {!token ? (
          <section className="card auth-card">
            <div className="auth-tabs">
              <button
                className={`tab-btn ${authMode === 'login' ? 'active' : ''}`}
                onClick={() => { setAuthMode('login'); setUsername(''); setPassword(''); }}
              >
                Logowanie
              </button>
              <button
                className={`tab-btn ${authMode === 'register' ? 'active' : ''}`}
                onClick={() => { setAuthMode('register'); setUsername(''); setPassword(''); }}
              >
                Rejestracja
              </button>
            </div>

            {authMode === 'login' ? (
              <form className="auth-form" onSubmit={handleLogin}>
                <input
                  type="text"
                  className="input"
                  placeholder="Nazwa użytkownika"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
                <input
                  type="password"
                  className="input"
                  placeholder="Hasło"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
                <button className="btn btn-primary" type="submit" disabled={loading}>
                  {loading ? 'Logowanie...' : 'Zaloguj'}
                </button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={handleRegister}>
                <input
                  type="text"
                  className="input"
                  placeholder="Nazwa użytkownika"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
                <input
                  type="password"
                  className="input"
                  placeholder="Hasło"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
                <button className="btn btn-primary" type="submit" disabled={loading}>
                  {loading ? 'Rejestracja...' : 'Zarejestruj'}
                </button>
              </form>
            )}
          </section>
        ) : (
          <section className="card create-post-card">
            <h2 className="section-title">Nowy post</h2>
            <form onSubmit={handleCreatePost}>
              <textarea
                className="input textarea"
                placeholder="Co słychać?"
                value={postContent}
                onChange={e => setPostContent(e.target.value)}
                rows={3}
                required
              />
              <button
                className="btn btn-primary"
                type="submit"
                disabled={loading || !postContent.trim()}
              >
                {loading ? 'Wysyłanie...' : 'Opublikuj'}
              </button>
            </form>
          </section>
        )}

        <section className="posts-section">
          <h2 className="section-title">Najnowsze posty</h2>
          {posts.length === 0 ? (
            <p className="no-posts">Brak postów. Bądź pierwszy!</p>
          ) : (
            posts.map(post => (
              <div key={post.id} className="card post-card">
                <div className="post-header">
                  <span className="post-username">{post.username}</span>
                  <span className="post-date">
                    {new Date(post.created_at).toLocaleString('pl-PL')}
                  </span>
                </div>

                {editingPostId === post.id ? (
                  <div className="post-edit">
                    <textarea
                      className="input textarea"
                      value={editContent}
                      onChange={e => setEditContent(e.target.value)}
                      rows={3}
                    />
                    <div className="post-actions">
                      <button className="btn btn-primary btn-sm" onClick={() => handleUpdatePost(post.id)}>Zapisz</button>
                      <button className="btn btn-outline btn-sm" onClick={() => setEditingPostId(null)}>Anuluj</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="post-content">{post.content}</p>
                    {token && currentUserId === post.user_id && (
                      <div className="post-actions">
                        <button className="btn btn-outline btn-sm" onClick={() => startEdit(post)}>Edytuj</button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeletePost(post.id)}>Usuń</button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </section>
      </main>
    </div>
  );
}

export default App;