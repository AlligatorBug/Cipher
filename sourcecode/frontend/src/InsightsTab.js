import { useState, useEffect } from 'react';

const UNLOCK_THRESHOLD = 20;

function InsightsTab({ user }) {
  const [insights, setInsights] = useState(null);
  const [txCount, setTxCount] = useState(0);
  const [loading, setLoading] = useState(true);

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

  if (loading) return <p style={{ textAlign: 'center', color: '#999', padding: '40px 0', fontSize: '13px' }}>Loading...</p>;

  if (!insights || txCount < UNLOCK_THRESHOLD) {
    const progress = Math.min(txCount / UNLOCK_THRESHOLD, 1);
    return (
      <div style={{ padding: '40px 24px', textAlign: 'center', paddingBottom: '80px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
        <p style={{ fontSize: '16px', fontWeight: '500', color: '#1A1A1A', marginBottom: '8px' }}>Archetype locked</p>
        <p style={{ fontSize: '13px', color: '#666', lineHeight: '1.6', marginBottom: '24px' }}>
          Add {UNLOCK_THRESHOLD - txCount} more transactions to unlock your spending archetype and behavioural insights.
        </p>
        <div style={{ background: '#F5F5F5', borderRadius: '100px', height: '8px', marginBottom: '8px', overflow: 'hidden' }}>
          <div style={{ background: '#D4537E', height: '100%', width: `${progress * 100}%`, borderRadius: '100px', transition: 'width 0.3s' }} />
        </div>
        <p style={{ fontSize: '12px', color: '#999' }}>{txCount} / {UNLOCK_THRESHOLD} transactions</p>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '80px' }}>
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
  );
}

export default InsightsTab;