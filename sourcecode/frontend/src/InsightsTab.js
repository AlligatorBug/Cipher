import { useState, useEffect } from 'react';

const UNLOCK_THRESHOLD = 20;

function InsightsTab({ user }) {
  const [activeSubtab, setActiveSubtab] = useState('insights');
  const [insights, setInsights] = useState(null);
  const [txCount, setTxCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const [category, setCategory] = useState('Food');
  const [timePeriod, setTimePeriod] = useState('last month');
  const [searchResult, setSearchResult] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const CATEGORIES = ['Food', 'Groceries', 'Transport', 'Shopping', 'Entertainment', 'Health', 'Subscriptions', 'Utilities'];
  const TIME_PERIODS = ['this month', 'last month', 'this year', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  useEffect(() => {
    fetchInsights();
  }, []);

  async function fetchInsights() {
    setLoading(true);
    try {
      const token = localStorage.getItem('cipher_token');
      const res = await fetch('http://localhost:8000/insights', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTxCount(data.transaction_count || 0);
      if (data.unlocked) setInsights(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    setSearchLoading(true);
    setSearchResult(null);
    try {
      const token = localStorage.getItem('cipher_token');
      const res = await fetch(`http://localhost:8000/search?category=${encodeURIComponent(category)}&period=${encodeURIComponent(timePeriod)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setSearchResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  }

  function clearSearch() {
    setSearchResult(null);
  }

  const subtabStyle = (tab) => ({
    flex: 1,
    padding: '7px 0',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontFamily: 'inherit',
    cursor: 'pointer',
    background: activeSubtab === tab ? '#D4537E' : 'transparent',
    color: activeSubtab === tab ? 'white' : '#999',
    fontWeight: activeSubtab === tab ? '500' : '400',
  });

  return (
    <div style={{ paddingBottom: '80px' }}>
      {/* subtab toggle */}
      <div style={{ padding: '12px 16px', borderBottom: '0.5px solid #E0E0E0' }}>
        <div style={{ display: 'flex', background: '#F5F5F5', borderRadius: '10px', padding: '3px', gap: '3px' }}>
          <button style={subtabStyle('insights')} onClick={() => setActiveSubtab('insights')}>Insights</button>
          <button style={subtabStyle('ask')} onClick={() => setActiveSubtab('ask')}>Ask Cipher</button>
        </div>
      </div>

      {activeSubtab === 'ask' && (
        <div style={{ padding: '16px' }}>
          <p style={{ fontSize: '12px', color: '#999', margin: '0 0 10px' }}>How much did I spend on</p>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <select
              value={category}
              onChange={e => { setCategory(e.target.value); setSearchResult(null); }}
              style={{ flex: 1, padding: '10px 12px', borderRadius: '10px', border: '0.5px solid #E0E0E0', background: '#F5F5F5', fontSize: '13px', fontFamily: 'inherit', outline: 'none', cursor: 'pointer' }}
            >
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
            <select
              value={timePeriod}
              onChange={e => { setTimePeriod(e.target.value); setSearchResult(null); }}
              style={{ flex: 1, padding: '10px 12px', borderRadius: '10px', border: '0.5px solid #E0E0E0', background: '#F5F5F5', fontSize: '13px', fontFamily: 'inherit', outline: 'none', cursor: 'pointer' }}
            >
              {TIME_PERIODS.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <button
            onClick={searchResult ? clearSearch : handleSearch}
            disabled={searchLoading}
            style={{ width: '100%', padding: '10px', borderRadius: '10px', border: 'none', background: searchResult ? '#E0E0E0' : '#D4537E', color: searchResult ? '#666' : 'white', fontSize: '13px', cursor: 'pointer', fontFamily: 'inherit', marginBottom: '16px' }}
          >
            {searchLoading ? 'Searching...' : searchResult ? 'Clear' : 'Search'}
          </button>

          {!searchResult && !searchLoading && (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <p style={{ fontSize: '28px', marginBottom: '8px' }}>💬</p>
              <p style={{ fontSize: '13px', color: '#999' }}>Select a category and time period above</p>
            </div>
          )}

          {searchLoading && (
            <p style={{ textAlign: 'center', color: '#999', fontSize: '13px', padding: '40px 0' }}>Thinking...</p>
          )}

          {searchResult && (
            <div>
              <div style={{ background: '#FFF0F5', borderRadius: '12px', padding: '12px 14px', marginBottom: '16px' }}>
                <p style={{ fontSize: '12px', color: '#D4537E', fontWeight: '500', margin: '0 0 6px' }}>Cipher</p>
                <p style={{ fontSize: '13px', color: '#1A1A1A', margin: 0, lineHeight: '1.5' }}>{searchResult.answer}</p>
              </div>

              {searchResult.transactions?.length > 0 && (
                <div>
                  <p style={{ fontSize: '11px', color: '#999', letterSpacing: '0.05em', margin: '0 0 8px' }}>MATCHING TRANSACTIONS</p>
                  {searchResult.transactions.map((tx, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < searchResult.transactions.length - 1 ? '0.5px solid #E0E0E0' : 'none' }}>
                      <div>
                        <p style={{ fontSize: '13px', color: '#1A1A1A', margin: 0 }}>{tx.description}</p>
                        <p style={{ fontSize: '11px', color: '#999', margin: 0 }}>{tx.predicted_category} · {tx.date}</p>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '500', color: '#D4537E' }}>-${tx.amount?.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeSubtab === 'insights' && loading && (
        <p style={{ textAlign: 'center', color: '#999', padding: '40px 0', fontSize: '13px' }}>Loading...</p>
      )}

      {activeSubtab === 'insights' && !loading && (!insights || txCount < UNLOCK_THRESHOLD) && (
        <div style={{ padding: '40px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
          <p style={{ fontSize: '16px', fontWeight: '500', color: '#1A1A1A', marginBottom: '8px' }}>Archetype locked</p>
          <p style={{ fontSize: '13px', color: '#666', lineHeight: '1.6', marginBottom: '24px' }}>
            Add {UNLOCK_THRESHOLD - txCount} more transactions to unlock your spending archetype and behavioural insights.
          </p>
          <div style={{ background: '#F5F5F5', borderRadius: '100px', height: '8px', marginBottom: '8px', overflow: 'hidden' }}>
            <div style={{ background: '#D4537E', height: '100%', width: `${Math.min(txCount / UNLOCK_THRESHOLD, 1) * 100}%`, borderRadius: '100px', transition: 'width 0.3s' }} />
          </div>
          <p style={{ fontSize: '12px', color: '#999' }}>{txCount} / {UNLOCK_THRESHOLD} transactions</p>
        </div>
      )}

      {activeSubtab === 'insights' && !loading && insights && txCount >= UNLOCK_THRESHOLD && (
        <div>
          <div style={{ padding: '16px', borderBottom: '0.5px solid #E0E0E0' }}>
            <p style={{ fontSize: '11px', color: '#D4537E', letterSpacing: '0.1em', margin: '0 0 6px', fontWeight: '500' }}>YOUR SPENDING ARCHETYPE</p>
            <p style={{ fontSize: '20px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 8px' }}>{insights.archetype}</p>
            <p style={{ fontSize: '13px', color: '#666', lineHeight: '1.6', margin: 0 }}>{insights.portrait}</p>
          </div>

          <div style={{ padding: '12px 16px', borderBottom: '0.5px solid #E0E0E0' }}>
            <p style={{ fontSize: '13px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 10px' }}>Key metrics</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '8px' }}>
              {insights.metrics?.map((m, i) => (
                <div key={i} style={{ background: '#F5F5F5', borderRadius: '10px', padding: '10px' }}>
                  <p style={{ fontSize: '11px', color: '#999', margin: '0 0 4px' }}>{m.label}</p>
                  <p style={{ fontSize: '20px', fontWeight: '500', color: m.color, margin: 0 }}>{m.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: '12px 16px' }}>
            <p style={{ fontSize: '13px', fontWeight: '500', color: '#1A1A1A', margin: '0 0 10px' }}>Behavioural insights</p>
            {insights.insights?.map((insight, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', padding: '8px 0', borderBottom: i < insights.insights.length - 1 ? '0.5px solid #E0E0E0' : 'none' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: insight.color, flexShrink: 0, marginTop: '4px' }} />
                <p style={{ fontSize: '13px', color: '#444', margin: 0, lineHeight: '1.55' }}>
                  <span style={{ fontWeight: '500', color: '#1A1A1A' }}>{insight.label}</span>
                  {' — '}{insight.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default InsightsTab;
