import { useState, useEffect } from 'react';

const CATEGORY_COLORS = {
  Food: '#FF6B6B',
  Groceries: '#FF9F43',
  Transport: '#FFD93D',
  Shopping: '#6BCB77',
  Entertainment: '#4D96FF',
  Health: '#9B5DE5',
  Subscriptions: '#F15BB5',
  Utilities: '#00BBF9',
  Others: '#999999',
};

const CATEGORY_ICONS = {
  Food: '🍜',
  Groceries: '🛒',
  Transport: '🚌',
  Shopping: '🛍️',
  Entertainment: '🎮',
  Health: '💊',
  Subscriptions: '📱',
  Utilities: '💡',
  Others: '📦',
};

function TransactionsTab({ user, onRefresh }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [expandedTx, setExpandedTx] = useState(null);
  const [editingTx, setEditingTx] = useState(null);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  useEffect(() => {
    fetchTransactions();
  }, [currentMonth]);

  async function fetchTransactions() {
    setLoading(true);
    try {
      const token = localStorage.getItem('cipher_token');
      const res = await fetch(`http://localhost:8000/transactions?month=${month + 1}&year=${year}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(txId) {
    try {
      const token = localStorage.getItem('cipher_token');
      await fetch(`http://localhost:8000/transactions/${txId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setExpandedTx(null);
      fetchTransactions();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
    }
  }

  const totalSpent = transactions.reduce((sum, tx) => sum + tx.amount, 0);
  const monthName = currentMonth.toLocaleDateString('en-SG', { month: 'long', year: 'numeric' });

  const grouped = {};
  transactions.forEach(tx => {
    if (!grouped[tx.date]) grouped[tx.date] = [];
    grouped[tx.date].push(tx);
  });
  const sortedDates = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  function formatDateHeader(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-SG', { day: 'numeric', month: 'short' }).toUpperCase();
  }

  return (
    <div style={{ paddingBottom: '80px' }}>
      <div style={{ padding: '16px', borderBottom: '0.5px solid #E0E0E0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <button onClick={() => setCurrentMonth(new Date(year, month - 1, 1))} style={{ background: 'none', border: 'none', color: '#D4537E', fontSize: '18px', cursor: 'pointer', padding: '0' }}>‹</button>
            <span style={{ fontSize: '13px', color: '#666' }}>{monthName}</span>
            <button onClick={() => setCurrentMonth(new Date(year, month + 1, 1))} style={{ background: 'none', border: 'none', color: '#D4537E', fontSize: '18px', cursor: 'pointer', padding: '0' }}>›</button>
          </div>
          <span style={{ fontSize: '22px', fontWeight: '500', color: '#1A1A1A' }}>${totalSpent.toFixed(2)}</span>
        </div>
      </div>

      {loading ? (
        <p style={{ textAlign: 'center', color: '#999', padding: '40px 0', fontSize: '13px' }}>Loading...</p>
      ) : transactions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 24px' }}>
          <p style={{ fontSize: '32px', marginBottom: '8px' }}>📭</p>
          <p style={{ fontSize: '14px', fontWeight: '500', color: '#1A1A1A', marginBottom: '4px' }}>No transactions yet</p>
          <p style={{ fontSize: '13px', color: '#999' }}>Tap + to add one or import your bank statement</p>
        </div>
      ) : (
        <div style={{ padding: '12px 16px' }}>
          {sortedDates.map(date => (
            <div key={date} style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '11px', color: '#999', letterSpacing: '0.05em', margin: '0 0 8px' }}>{formatDateHeader(date)}</p>
              {grouped[date].map((tx, i) => {
                const cat = tx.predicted_category || tx.category || 'Others';
                const color = CATEGORY_COLORS[cat] || '#999';
                const isExpanded = expandedTx === tx.id;

                return (
                  <div key={i}>
                    <div
                      onClick={() => setExpandedTx(isExpanded ? null : tx.id)}
                      style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: !isExpanded && i < grouped[date].length - 1 ? '0.5px solid #E0E0E0' : 'none', cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: color + '20', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }}>
                          {CATEGORY_ICONS[cat] || '📦'}
                        </div>
                        <div>
                          <p style={{ fontSize: '13px', color: '#1A1A1A', margin: 0 }}>{tx.description}</p>
                          <p style={{ fontSize: '11px', color: '#999', margin: 0 }}>{cat}{tx.time ? ` · ${tx.time}` : ''}</p>
                        </div>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '500', color: '#D4537E' }}>-${tx.amount.toFixed(2)}</span>
                    </div>

                    {isExpanded && (
                      <div style={{ display: 'flex', gap: '8px', padding: '8px 0 12px', borderBottom: i < grouped[date].length - 1 ? '0.5px solid #E0E0E0' : 'none' }}>
                        <button
                          onClick={() => setEditingTx(tx)}
                          style={{ flex: 1, padding: '8px', background: '#F5F5F5', border: 'none', borderRadius: '8px', fontSize: '13px', color: '#1A1A1A', cursor: 'pointer', fontFamily: 'inherit' }}
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(tx.id)}
                          style={{ flex: 1, padding: '8px', background: '#FBEAF0', border: 'none', borderRadius: '8px', fontSize: '13px', color: '#D4537E', cursor: 'pointer', fontFamily: 'inherit' }}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          <div style={{ background: '#F5F5F5', borderRadius: '10px', padding: '10px 14px', display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
            {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
              <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
                <span style={{ fontSize: '11px', color: '#666' }}>{cat}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {editingTx && (
        <EditModal
          tx={editingTx}
          onClose={() => setEditingTx(null)}
          onSaved={() => {
            setEditingTx(null);
            setExpandedTx(null);
            fetchTransactions();
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </div>
  );
}

function EditModal({ tx, onClose, onSaved }) {
  const [description, setDescription] = useState(tx.description);
  const [amount, setAmount] = useState(tx.amount);
  const [category, setCategory] = useState(tx.category || tx.predicted_category || 'Food');
  const [date, setDate] = useState(tx.date);
  const [time, setTime] = useState(tx.time || '');
  const [loading, setLoading] = useState(false);

  async function handleSave() {
    setLoading(true);
    try {
      const token = localStorage.getItem('cipher_token');
      await fetch(`http://localhost:8000/transactions/${tx.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ description, amount: parseFloat(amount), category, date, time })
      });
      onSaved();
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
          <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#1A1A1A', margin: 0 }}>Edit transaction</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#999' }}>×</button>
        </div>
        <div className="form-group">
          <input className="input" placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} />
          <div className="form-row">
            <input className="input" placeholder="Amount" type="number" value={amount} onChange={e => setAmount(e.target.value)} />
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
          <select className="input" value={time} onChange={e => setTime(e.target.value)}>
            <option value="">Time of day (optional)</option>
            <option value="morning">Morning (6am–12pm)</option>
            <option value="afternoon">Afternoon (12pm–6pm)</option>
            <option value="evening">Evening (6pm–10pm)</option>
            <option value="late night">Late night (10pm–6am)</option>
          </select>
        </div>
        <button className="btn-pink" style={{ width: '100%', marginTop: '8px' }} onClick={handleSave} disabled={loading}>
          {loading ? 'Saving...' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}

export default TransactionsTab;