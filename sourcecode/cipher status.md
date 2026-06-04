# Cipher — Project Status

## Tech Stack

|Layer     |Tech                                                |
|----------|----------------------------------------------------|
|Frontend  |React (PWA, mobile-first)                           |
|Backend   |FastAPI (Python)                                    |
|Database  |PostgreSQL (Neon)                                   |
|Auth      |Neon Auth (Stack Auth under the hood)               |
|ML        |scikit-learn, sentence-transformers, FAISS (planned)|
|LLM       |Groq API (archetypes), Claude API (portraits)       |
|Deployment|Vercel (frontend) + Railway (FastAPI)               |

-----

## What’s Done ✅

### Infrastructure

- [x] React frontend — baseline UI
- [x] FastAPI backend
- [x] PostgreSQL database (Neon)
- [x] Authentication (Neon Auth / Stack Auth)
- [x] PDF parser (pdfplumber) — parses DBS, OCBC, UOB formats, extracts date/description/amount columns
- [x] Frontend ↔ backend connected end to end
- [x] GitHub repo set up

### ML / Features

- [x] Transaction categorisation — TF-IDF + logistic regression (working, current baseline)
- [x] Spending archetype generation — Groq API call (rule-based, not real ML)
- [x] Basic insights section (exists, details TBC)

### Product

- [x] 6 behavioural archetypes defined with academic grounding (Kahneman, Thaler, Ariely):
  - Present Hedonist
  - Comfort Seeker
  - Status Signaller
  - Anxious Saver
  - Optimism Spender
  - Inertia Holder

-----

## What’s Next — ML Upgrade Roadmap 🚀

### Phase 1 — Smarter Categorisation (do this weekend)

**Upgrade TF-IDF → sentence transformers (zero-shot)**

No training data needed. Embed transaction descriptions + category labels, pick closest match by cosine similarity.

```python
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')
# embed categories once, compare each transaction at runtime
```

- [x] Install sentence-transformers
- [x] Replace TF-IDF vectoriser with zero-shot sentence transformer pipeline
- [x] Test on existing transaction data, identify failure cases (Singapore merchants like Koufu, NTUC, EZ-Link)
- [x] If consistent errors → fine-tune on those specific cases

-----

### Phase 2 — Transaction Search

**Structured category + time period search over user’s transactions**

feature: user selects category + time period → DB filters by predicted_category and date → LLM summarises total → show answer + matching transactions

- [x] Build search endpoint in FastAPI (GET /search?category=&period=)
- [x] Connect to frontend as “Ask Cipher” subtab in Insights
- [x] Date parsing for last month / this month / this year / named months
-----

### Phase 3 — Spending Forecasting

**Predict end-of-month spend per category**

Linear regression or moving average over monthly aggregated totals. No external training data — fit on user’s own history.

- [ ] Aggregate transactions into monthly totals per category
- [ ] Fit linear regression (sklearn) on user’s history
- [ ] Show “you’re on track to spend $X on food this month”
- [ ] Handle cold start (< 2 months data) gracefully

-----

### Phase 4 — Anomaly Detection

**Flag unusual transactions**

Isolation forest or DBSCAN on user’s transaction history. Unsupervised, no labels needed.

- [ ] Flag transactions that are outliers vs user’s typical spending
- [ ] Surface as alerts: “this coffee was 3x your usual”
- [ ] Detect duplicate charges

-----

### Phase 5 — Real Archetype Clustering (replace Groq API)

**Replace rule-based archetypes with actual ML clustering**

DBSCAN or KMeans on behavioural features extracted from transaction history.

- [ ] Feature engineering: late-night spend %, impulse purchase flags, category ratios, spend variance
- [ ] Cluster users into archetypes using DBSCAN
- [ ] Map clusters to the 6 defined archetypes
- [ ] Keep Groq/Claude API at the end to narrate the ML output in human language

-----

## Product Roadmap (Versions)

|Version|Theme                                                                               |Status     |
|-------|------------------------------------------------------------------------------------|-----------|
|V1     |Decode yourself — stateless, no login, upload CSV/PDF, get archetype                |~done      |
|V2     |Understand yourself — user accounts, longitudinal tracking, Cipher Wrapped          |in progress|
|V3     |Change yourself — nudges, commitment devices, peer benchmarking                     |planned    |
|V4     |Recommend for yourself — behaviourally matched product recommendations, monetisation|future     |
-----

## Key Numbers

- 3-person team
- React + FastAPI + PostgreSQL + sentence-transformers + FAISS
- PDF parsing for DBS, OCBC, UOB formats
- 6 behavioural archetypes grounded in Kahneman/Thaler/Ariely research