import { useState } from 'react';
import './App.css';

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit() {
    if (!email || !password) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Something went wrong');
        return;
      }

      localStorage.setItem('cipher_token', data.token);
      localStorage.setItem('cipher_user_id', data.user_id);
      localStorage.setItem('cipher_email', data.email);
      onLogin(data);

    } catch (err) {
      setError('Could not connect to server.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <div className="card">

        {/* logo */}
        <div className="logo-container">
          <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
            <rect x="2" y="30" width="7" height="14" rx="2" fill="#C8E6C9"/>
            <rect x="11" y="22" width="7" height="22" rx="2" fill="#81C784"/>
            <rect x="20" y="14" width="7" height="30" rx="2" fill="#2E7D32"/>
            <rect x="29" y="18" width="7" height="26" rx="2" fill="#81C784"/>
            <rect x="38" y="26" width="7" height="18" rx="2" fill="#C8E6C9"/>
            <circle cx="24" cy="8" r="7" fill="#D4537E"/>
            <circle cx="21.5" cy="7" r="1.3" fill="white"/>
            <circle cx="26.5" cy="7" r="1.3" fill="white"/>
            <path d="M21.5 10.5 Q24 12.5 26.5 10.5" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </div>

        <p className="label">CIPHER · BEHAVIOURAL FINANCE</p>
        <h1 className="headline">Decode your<br/>spending<br/>psychology.</h1>
        <p className="tagline" style={{ marginBottom: '16px' }}> Track your spending and discover what it reveals about you — grounded in real behavioural science.</p>

        {/* auth form */}
        <div className="form-group" style={{ width: '100%', marginBottom: '0' }}>
          <input
            className="input"
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="input"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="error-msg" style={{ width: '100%' }}>{error}</p>}

        <button
          className="btn-pink"
          style={{ width: '100%', marginTop: '8px' }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Please wait...' : mode === 'login' ? 'Log in →' : 'Create account →'}
        </button>

        <p className="demo-link" style={{ marginTop: '16px', marginBottom: '16px' }}>
          {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
          <span onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}>
            {mode === 'login' ? 'Sign up' : 'Log in'}
          </span>
        </p>

        <div className="divider" />

        <div className="stats">
          <div className="stat">
            <p className="stat-number pink">6</p>
            <p className="stat-label">archetypes</p>
          </div>
          <div className="stat-divider" />
          <div className="stat">
            <p className="stat-number green">15+</p>
            <p className="stat-label">behavioural signals</p>
          </div>
          <div className="stat-divider" />
          <div className="stat">
            <p className="stat-number dark">SG</p>
            <p className="stat-label">built for Singapore</p>
          </div>
        </div>

      </div>
    </div>
  );
}

export default AuthScreen;