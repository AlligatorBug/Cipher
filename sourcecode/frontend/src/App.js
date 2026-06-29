import { useState, useEffect } from 'react';
import AuthScreen from './AuthScreen';
import HomeScreen from './HomeScreen';
import AgentChat from './AgentChat'
import './App.css';

function App() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('cipher_token');
    const email = localStorage.getItem('cipher_email');
    return token ? { token, email } : null;
  });

  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_URL}/health`).catch(() => {});
  }, []);

  function handleLogin(data) {
    setUser(data);
  }

  function handleLogout() {
    localStorage.removeItem('cipher_token');
    localStorage.removeItem('cipher_user_id');
    localStorage.removeItem('cipher_email');
    setUser(null);
  }

  if (!user) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  return (
    <>
      <HomeScreen user={user} onLogout={handleLogout} />
      <AgentChat user={user} />
    </>
  );
}

export default App;