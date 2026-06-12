# Cipher

Cipher is a behavioural finance web app that tells you *why* you spend the way you do — not just what you spend on.

Upload a bank statement PDF and Cipher categorises your transactions, assigns you a spending archetype grounded in behavioural economics, forecasts your end-of-month spend, and generates a plain-language portrait of your financial psychology.

---

## Features

- **PDF import** — parses Citibank and Amex credit card statements
- **Smart categorisation** — sentence-transformer + logistic regression classifier trained on Singapore merchants
- **Spending archetypes** — 6 psychologically-grounded profiles (Present Hedonist, Comfort Seeker, Status Signaller, Anxious Saver, Optimism Spender, Inertia Holder) rooted in Kahneman, Thaler, and Ariely
- **Forecasting** — linear regression on your own transaction history to predict end-of-month spend per category
- **Anomaly detection** — Isolation Forest flags unusually high charges relative to your personal baseline
- **Ask Cipher** — query your spending by category and time period in plain language
- **Secure auth** — JWT authentication, bcrypt password hashing

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Vercel |
| Backend | FastAPI (Python), Railway |
| Database | PostgreSQL (Neon) |
| ML | scikit-learn, sentence-transformers |
| LLM | OpenAI API (gpt-4o-mini) |

## Local Setup

**Backend**
```bash
cd sourcecode/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd sourcecode/frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000" > .env
npm start
```

**Environment variables (backend `.env`)**
```
DATABASE_URL=
JWT_SECRET=
OPENAI_API_KEY=
FRONTEND_URL=
```
