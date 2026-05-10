import { useNavigate, useSearchParams } from 'react-router-dom';
import { useState } from 'react';
import './App.css';

function UploadScreen() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode');

  // state for manual entry
  const [transactions, setTransactions] = useState([]);
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Food');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [time, setTime] = useState('');

  // state for CSV upload
  const [file, setFile] = useState(null);

  function addTransaction() {
    if (!description || !amount) return;
    const newTransaction = {
      description,
      amount: parseFloat(amount),
      category,
      time,
    };
    setTransactions([...transactions, newTransaction]);
    setDescription('');
    setAmount('');
    setTime('');
  }

  function handleFileChange(e) {
    setFile(e.target.files[0]);
  }

  async function handleAnalyse() {
    setLoading(true); // show spinner 
    setError(null);

    // fetch sends a request to that URL
    try {
      const response = await fetch('http://localhost:8000/analyse', {
        method: 'POST', // we're sending data, not just requesting it
        headers: { 'Content-Type': 'application/json' }, // tells FastAPI we're sending JSON
        body: JSON.stringify({ transactions }) // converts our JavaScript transactions array into a JSON string to send over the network
      });
  
      if (!response.ok) {
        throw new Error('Server error — please try again');
      }
      
      // await: tells JavaScript "pause here and wait for this to finish before moving on." -> needs to be in async fxn to work
      const data = await response.json(); // converts FastAPI's response back from JSON into a JavaScript object we can use
      navigate('/results', { state: data });
  
    } catch (err) {
      setError('Could not connect to server. Make sure the backend is running.');
    } finally {
      setLoading(false); // hide spinner 
    }
  }

  return (
    <div className="app">
      <div className="card">

        <button className="back-btn" onClick={() => navigate('/')}>← Back</button>

        {mode === 'csv' ? (
          // CSV MODE
          <div>
            <h2 className="screen-title">Upload your CSV</h2>
            <p className="screen-subtitle">
              Export your transactions from your bank app and upload the file here.
            </p>

            <label className="upload-zone">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M12 16V8m0 0-3 3m3-3 3 3" stroke="#2E7D32" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                <rect x="3" y="3" width="18" height="18" rx="4" stroke="#C8E6C9" strokeWidth="1"/>
              </svg>
              {file ? (
                <p className="upload-filename">{file.name}</p>
              ) : (
                <>
                  <p className="upload-title">Drop your CSV here</p>
                  <p className="upload-hint">or click to browse</p>
                </>
              )}
            </label>

            <button
              className="btn-pink"
              disabled={!file || loading}
              style={{ opacity: file ? 1 : 0.4, width: '100%' }}
              onClick={handleAnalyse}
            >
              {loading ? 'Analysing...' : 'Analyse my spending →'}
            </button>
          </div>

        ) : (

          // MANUAL MODE
          <div>
            <h2 className="screen-title">Add transactions</h2>
            <p className="screen-subtitle">
              Add at least 10 transactions for accurate results.
            </p>

            <div className="form-group">
              <input
                className="input"
                placeholder="Description (e.g. McDonald's)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <div className="form-row">
                <input
                  className="input"
                  placeholder="Amount (SGD)"
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
                <select
                  className="input"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
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
              <select
                className="input"
                value={time}
                onChange={(e) => setTime(e.target.value)}
            >
                <option value="">Time of day (optional)</option>
                <option value="morning">Morning (6am–12pm)</option>
                <option value="afternoon">Afternoon (12pm–6pm)</option>
                <option value="evening">Evening (6pm–10pm)</option>
                <option value="late night">Late night (10pm–6am)</option>
            </select>
              <button className="btn-green" onClick={addTransaction}>
                + Add transaction
              </button>
            </div>

            <div className="tx-counter">
              {transactions.length === 0
                ? '0 transactions added — need at least 10'
                : `${transactions.length} transaction${transactions.length > 1 ? 's' : ''} added ${transactions.length < 10 ? `— need ${10 - transactions.length} more` : '✓ ready!'}`
              }
            </div>

            {transactions.length > 0 && (
              <div className="tx-list">
                {transactions.map((tx, index) => (
                    <div key={index} className="tx-item">
                        <div>
                        <p className="tx-desc">{tx.description}</p>
                        <p className="tx-cat">{tx.category}</p>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <p className="tx-amount">${tx.amount.toFixed(2)}</p>
                        <button
                            onClick={() => setTransactions(transactions.filter((_, i) => i !== index))}
                            style={{ background: 'none', border: 'none', color: '#999', cursor: 'pointer', fontSize: '16px', padding: '0' }}
                        >
                            ×
                        </button>
                        </div>
                    </div>
                ))}
              </div>
            )}

            {error && <p className="error-msg">{error}</p>}
            <button
              className="btn-pink"
              disabled={transactions.length < 10 || loading}
              style={{ opacity: transactions.length >= 10 ? 1 : 0.4, width: '100%', marginTop: '16px' }}
              onClick={handleAnalyse}
            >
              {loading ? 'Analysing...' : 'Analyse my spending →'}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

export default UploadScreen;