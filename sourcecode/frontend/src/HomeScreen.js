import { useState } from 'react';
import CalendarTab from './CalendarTab';
import TransactionsTab from './TransactionsTab';
import InsightsTab from './InsightsTab';
import ProfileTab from './ProfileTab';
import './App.css';

function HomeScreen({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('calendar');
  const [showAddModal, setShowAddModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0); 

  function triggerRefresh() { 
    setRefreshKey(k => k + 1);
    setShowAddModal(false);
  }

  return (
    <div className="app">
      <div style={{
        width: '390px',
        minWidth: '390px',
        height: '700px',
        background: '#FDFAF6',
        borderRadius: '24px',
        border: '0.5px solid #C8E6C9',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        }}>

        {/* tab content - scrollable */}
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '80px' }}>
          {activeTab === 'calendar' && <CalendarTab key={refreshKey} user={user} onAddPress={() => setShowAddModal(true)} />}
          {activeTab === 'transactions' && <TransactionsTab key={refreshKey} user={user} onRefresh={triggerRefresh} />}
          {activeTab === 'insights' && <InsightsTab user={user} />}
          {activeTab === 'profile' && <ProfileTab user={user} onLogout={onLogout} />}
        </div>

        {/* bottom tab bar - fixed */}
        <div style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          borderTop: '0.5px solid #E0E0E0',
          background: '#FDFAF6',
          padding: '8px 0 12px',
          zIndex: 10,
        }}>
          <div onClick={() => setActiveTab('calendar')} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', cursor: 'pointer', color: activeTab === 'calendar' ? '#D4537E' : '#999' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>

          <div onClick={() => setActiveTab('transactions')} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', cursor: 'pointer', color: activeTab === 'transactions' ? '#D4537E' : '#999' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          </div>

          {/* add button */}
          <div onClick={() => setShowAddModal(true)} style={{
            width: '48px', height: '48px',
            background: '#D4537E',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(212, 83, 126, 0.3)',
            }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </div>

          <div onClick={() => setActiveTab('insights')} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', cursor: 'pointer', color: activeTab === 'insights' ? '#D4537E' : '#999' }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          </div>

          <div onClick={() => setActiveTab('profile')} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', cursor: 'pointer', color: activeTab === 'profile' ? '#D4537E' : '#999' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
        </div>

        {/* add transaction modal */}
        {showAddModal && <AddModal onClose={() => setShowAddModal(false)} onAdded={triggerRefresh} user={user} />}
      </div>
    </div>
  );
}

function AddModal({ onClose, user, onAdded }) {
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Food');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);

  async function handleAdd() {
    if (!description || !amount) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('cipher_token');
      await fetch('http://localhost:8000/transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          description,
          amount: parseFloat(amount),
          category,
          date
        })
      });
      onAdded();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'flex-end',
      zIndex: 100,
    }} onClick={onClose}>
      <div style={{
        background: '#FDFAF6',
        borderRadius: '20px 20px 0 0',
        padding: '24px',
        width: '100%',
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#1A1A1A', margin: 0 }}>Add transaction</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#999' }}>×</button>
        </div>
        <div className="form-group">
          <input className="input" placeholder="Description (e.g. Grab Food)" value={description} onChange={e => setDescription(e.target.value)} />
          <div className="form-row">
            <input className="input" placeholder="Amount (SGD)" type="number" value={amount} onChange={e => setAmount(e.target.value)} />
            <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)} />
          </div>
          <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
            <option>Food</option>
            <option>Transport</option>
            <option>Shopping</option>
            <option>Groceries</option>
            <option>Entertainment</option>
            <option>Health</option>
            <option>Subscriptions</option>
            <option>Utilities</option>
            <option>Others</option>
          </select>
        </div>
        <button className="btn-pink" style={{ width: '100%', marginTop: '8px' }} onClick={handleAdd} disabled={loading}>
          {loading ? 'Adding...' : 'Add transaction'}
        </button>
      </div>
    </div>
  );
}

export default HomeScreen;