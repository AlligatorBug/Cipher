function ProfileTab({ user, onLogout }) {
  return (
    <div style={{ paddingBottom: '80px' }}>
      <div style={{ padding: '24px 16px 16px', borderBottom: '0.5px solid #E0E0E0', textAlign: 'center' }}>
        <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: '#FBEAF0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px' }}>
          <span style={{ fontSize: '20px', fontWeight: '500', color: '#D4537E' }}>
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </span>
        </div>
        <p style={{ fontSize: '15px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 2px' }}>{user?.email}</p>
        <p style={{ fontSize: '12px', color: '#999', margin: 0 }}>Member since May 2026</p>
      </div>

      <div style={{ padding: '12px 16px' }}>
        <p style={{ fontSize: '11px', color: '#999', letterSpacing: '0.05em', margin: '0 0 8px' }}>ACCOUNT</p>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '0.5px solid #E0E0E0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>🔔</span>
            <span style={{ fontSize: '13px', color: '#1A1A1A' }}>Notifications</span>
          </div>
          <span style={{ color: '#999', fontSize: '16px' }}>›</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '0.5px solid #E0E0E0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>🔒</span>
            <span style={{ fontSize: '13px', color: '#1A1A1A' }}>Change password</span>
          </div>
          <span style={{ color: '#999', fontSize: '16px' }}>›</span>
        </div>

        <p style={{ fontSize: '11px', color: '#999', letterSpacing: '0.05em', margin: '16px 0 8px' }}>ABOUT</p>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '0.5px solid #E0E0E0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>📋</span>
            <span style={{ fontSize: '13px', color: '#1A1A1A' }}>Privacy policy</span>
          </div>
          <span style={{ color: '#999', fontSize: '16px' }}>›</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '0.5px solid #E0E0E0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>ℹ️</span>
            <span style={{ fontSize: '13px', color: '#1A1A1A' }}>Version 1.0.0</span>
          </div>
        </div>

        <button
          onClick={onLogout}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 0', background: 'none', border: 'none', cursor: 'pointer', width: '100%', fontFamily: 'inherit' }}
        >
          <span style={{ fontSize: '18px' }}>🚪</span>
          <span style={{ fontSize: '13px', color: '#D4537E' }}>Log out</span>
        </button>
      </div>
    </div>
  );
}

export default ProfileTab;