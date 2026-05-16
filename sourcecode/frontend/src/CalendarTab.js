import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

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

function CalendarTab({ user, onAddPress }) {
  const [transactions, setTransactions] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  useEffect(() => {
    fetchTransactions();
  }, [currentMonth]);

  async function fetchTransactions() {
    try {
      const token = localStorage.getItem('cipher_token');
      const res = await fetch(`http://localhost:8000/transactions?month=${month + 1}&year=${year}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error(err);
    }
  }

  // group transactions by date
  const txByDate = {};
  transactions.forEach(tx => {
    if (!txByDate[tx.date]) txByDate[tx.date] = [];
    txByDate[tx.date].push(tx);
  });

  // calendar grid
  const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startOffset = firstDay === 0 ? 6 : firstDay - 1; // Mon-start

  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];

  const totalSpent = transactions.reduce((sum, tx) => sum + tx.amount, 0);

  const selectedTxs = selectedDate ? (txByDate[selectedDate] || []) : [];

  function prevMonth() {
    setCurrentMonth(new Date(year, month - 1, 1));
    setSelectedDate(null);
  }

  function nextMonth() {
    setCurrentMonth(new Date(year, month + 1, 1));
    setSelectedDate(null);
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-SG', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  const monthName = currentMonth.toLocaleDateString('en-SG', { month: 'long', year: 'numeric' });

  return (
    <div style={{ paddingBottom: '80px' }}>
      
      {/* header */}
      <div style={{ padding: '16px 16px 8px', borderBottom: '0.5px solid #E0E0E0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '13px', color: '#666' }}>{monthName}</span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button onClick={prevMonth} style={{ background: 'none', border: 'none', color: '#D4537E', fontSize: '18px', cursor: 'pointer', padding: '0 6px' }}>‹</button>
            <button onClick={nextMonth} style={{ background: 'none', border: 'none', color: '#D4537E', fontSize: '18px', cursor: 'pointer', padding: '0 6px' }}>›</button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'baseline' }}>
          <span style={{ fontSize: '22px', fontWeight: '500', color: '#1A1A1A' }}>${totalSpent.toFixed(2)}</span>
          <span style={{ fontSize: '13px', color: '#666' }}>spent this month</span>
        </div>
      </div>

      {/* calendar grid */}
      <div style={{ padding: '12px 16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', marginBottom: '8px' }}>
          {['M','T','W','T','F','S','S'].map((d, i) => (
            <div key={i} style={{ textAlign: 'center', fontSize: '11px', color: '#999', padding: '4px 0' }}>{d}</div>
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px' }}>
          {Array(startOffset).fill(null).map((_, i) => <div key={`empty-${i}`} />)}
          {Array(daysInMonth).fill(null).map((_, i) => {
            const day = i + 1;
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayTxs = txByDate[dateStr] || [];
            const dayTotal = dayTxs.reduce((sum, tx) => sum + tx.amount, 0);
            const isToday = dateStr === todayStr;
            const isSelected = dateStr === selectedDate;

            return (
              <div
                key={day}
                onClick={() => setSelectedDate(dateStr === selectedDate ? null : dateStr)}
                style={{
                    textAlign: 'center',
                    padding: '2px',
                    borderRadius: '50%',
                    background: isToday ? '#D4537E' : isSelected ? '#FBEAF0' : 'none',
                    cursor: 'pointer',
                    width: '32px',
                    height: '32px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                  }}
              >
                <span style={{ fontSize: '12px', color: isToday ? 'white' : '#1A1A1A', fontWeight: isToday ? '500' : '400' }}>{day}</span>
                {dayTotal > 0 && (
                  <div style={{ fontSize: '9px', color: isToday ? 'white' : '#D4537E', fontWeight: '500' }}>${dayTotal.toFixed(2)}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* import card */}
      <div style={{ padding: '0 16px 12px' }}>
        <div style={{ background: '#FBEAF0', borderRadius: '12px', padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '13px', fontWeight: '500', color: '#72243E', margin: '0 0 2px' }}>Import bank statement</p>
            <p style={{ fontSize: '11px', color: '#99354E', margin: 0 }}>Auto-fill your calendar with real data</p>
          </div>
          <button
            className="btn-pink"
            style={{ fontSize: '12px', padding: '8px 14px', width: 'auto', borderRadius: '20px' }}
            onClick={() => document.getElementById('pdf-upload').click()}
          >
            Upload PDF
          </button>
          <input id="pdf-upload" type="file" accept=".csv,.pdf" style={{ display: 'none' }} onChange={handleImport} />
        </div>
      </div>

      {/* spending summary */}
        {transactions.length > 0 && (() => {
        const categoryTotals = {};
        transactions.forEach(tx => {
            const cat = tx.predicted_category || tx.category || 'Others';
            categoryTotals[cat] = (categoryTotals[cat] || 0) + tx.amount;
        });

        const pieData = Object.entries(categoryTotals)
            .map(([name, value]) => ({ name, value: parseFloat(value.toFixed(2)) }))
            .sort((a, b) => b.value - a.value);

        const top3 = pieData.slice(0, 3);
        const total = transactions.reduce((sum, tx) => sum + tx.amount, 0);

        return (
            <div style={{ padding: '0 16px 12px' }}>
            <div style={{ background: 'white', borderRadius: '12px', border: '0.5px solid #E0E0E0', padding: '14px 16px' }}>
                <p style={{ fontSize: '13px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 12px' }}>Spending breakdown</p>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                {/* pie chart */}
                <div style={{ width: '100px', height: '100px', flexShrink: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={28}
                        outerRadius={46}
                        paddingAngle={2}
                        dataKey="value"
                        >
                        {pieData.map((entry, index) => (
                            <Cell key={index} fill={CATEGORY_COLORS[entry.name] || '#999'} />
                        ))}
                        </Pie>
                    </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* top 3 */}
                <div style={{ flex: 1 }}>
                    {top3.map((cat, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: i < 2 ? '8px' : '0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: CATEGORY_COLORS[cat.name] || '#999', flexShrink: 0 }} />
                        <span style={{ fontSize: '12px', color: '#666' }}>{cat.name}</span>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '12px', fontWeight: '500', color: '#1A1A1A' }}>${cat.value.toFixed(2)}</span>
                        <span style={{ fontSize: '11px', color: '#999', marginLeft: '4px' }}>{Math.round(cat.value / total * 100)}%</span>
                        </div>
                    </div>
                    ))}
                </div>
                </div>
            </div>
            </div>
        );
        })()}

      {/* selected day transactions */}
      {selectedDate && (
        <div style={{ borderTop: '0.5px solid #E0E0E0', padding: '12px 16px' }}>
          <p style={{ fontSize: '13px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 10px' }}>{formatDate(selectedDate)}</p>
          {selectedTxs.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#999', textAlign: 'center', padding: '16px 0' }}>No transactions this day</p>
          ) : (
            selectedTxs.map((tx, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < selectedTxs.length - 1 ? '0.5px solid #E0E0E0' : 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: CATEGORY_COLORS[tx.predicted_category || tx.category] || '#999', flexShrink: 0 }} />
                  <div>
                    <p style={{ fontSize: '13px', color: '#1A1A1A', margin: 0 }}>{tx.description}</p>
                    <p style={{ fontSize: '11px', color: '#999', margin: 0 }}>{tx.predicted_category || tx.category}</p>
                  </div>
                </div>
                <span style={{ fontSize: '13px', fontWeight: '500', color: '#D4537E' }}>-${tx.amount.toFixed(2)}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );

  async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
      const token = localStorage.getItem('cipher_token');
      
      if (file.name.endsWith('.pdf')) {
        const formData = new FormData();
        formData.append('file', file);
        const parseRes = await fetch('http://localhost:8000/parse-pdf', {
          method: 'POST',
          body: formData
        });
        const parseData = await parseRes.json();
        console.log('parsed data:', parseData); // ← add this
        if (parseData.error) {
          console.log('parse error:', parseData.error); // ← add this
          return;
        }
        
        const bulkRes = await fetch('http://localhost:8000/transactions/bulk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ transactions: parseData.transactions })
        });
        console.log('bulk result:', await bulkRes.json()); // ← add this
      }
      fetchTransactions();
    } catch (err) {
      console.error('import error:', err);
    }
  }
}

export default CalendarTab;