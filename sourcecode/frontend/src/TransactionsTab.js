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

function TransactionsTab({ user }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());

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

  const totalSpent = transactions.reduce((sum, tx) => sum + tx.amount, 0);
  const monthName = currentMonth.toLocaleDateString('en-SG', { month: 'long', year: 'numeric' });

  // group by date
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
                return (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < grouped[date].length - 1 ? '0.5px solid #E0E0E0' : 'none' }}>
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
    </div>
  );
}

export default TransactionsTab;