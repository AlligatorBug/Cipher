from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import pdfplumber
from dotenv import load_dotenv
import os
import io
from pydantic import BaseModel
from categoriser import categorise_transactions
from features import extract_features 
from archetypes import assign_archetype, generate_insights
from auth import hash_password, verify_password, create_token, decode_token
from database import get_db, SessionLocal
from sqlalchemy import text
import uuid
from forecast import forecast_next_month

app = FastAPI() # creates FastAPI server 
load_dotenv() # loads .env file 

"""
localhost:8000/health → runs health()
localhost:8000/analyse → runs analyse()
localhost:8000/parse-pdf → runs parse_pdf()
"""

# ── allow React (localhost:3000) to talk to FastAPI (localhost:8000) ──
app.add_middleware(
    CORSMiddleware,  
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── data models ──
# BaseModel is a Pydantic class that provides data validation and parsing, defines shape of the data coming in 
# when React sends transactions, FastAPI automatically validates they have a description, amount, and category, if not reject 
class Transaction(BaseModel):
    description: str
    amount: float
    category: str = ""
    time: str = ""
    date: str = ""

class AnalyseRequest(BaseModel):
    transactions: List[Transaction]

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ── helper to get current user from token ──
# every endpoint calls this 
# authorisation = stores JWT token (sends with every request from frontend)
# backend verifies token, extracts user_id and knows who is making the request
def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user_id = decode_token(token)
        return user_id
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── health check endpoint ──
# when someone hits GET /health, run this fxn
@app.get("/health")
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    finally:
        db.close()

# ── main analyse endpoint ──
# when React sends transactions to POST /analyse, this function runs and returns the mock results
@app.post("/analyse")
def analyse(request: AnalyseRequest):
    # categorise the transactions
    transactions_list = [t.dict() for t in request.transactions]
    categorised = categorise_transactions(transactions_list)
    features = extract_features(categorised)
    archetype_name, archetype_data, scores = assign_archetype(features)
    insights = generate_insights(features, archetype_name)

    # count spending by category
    # cat = category name
    category_totals = {}
    for tx in categorised:
        cat = tx["predicted_category"]
        category_totals[cat] = category_totals.get(cat, 0) + tx["amount"] #.get(cat, 0) returns current total for category or 0 if not exists

    # sort by amount
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    # category_totals.items() returns list of (category, total) pairs, sorted by total in descending order
    # key = lambda x: x[1] tells sorted() to sort by the second element of the pair (the total amount)
    # reverse=True sorts in descending order so highest spending categories come first
    top_categories = sorted_categories[:5] # takes only the first 5 items 

    # build chart data from real transactions
    chart_colors = ["#D4537E", "#81C784", "#2E7D32", "#ED93B1", "#C8E6C9"]
    chart_data = {
        "labels": [c[0] for c in top_categories],
        "values": [round(c[1], 2) for c in top_categories],
        "colors": chart_colors[:len(top_categories)]
    }

    # total spent
    total_spent = sum(tx["amount"] for tx in categorised)
    
    return {
        "archetype": archetype_name,
        "portrait": generate_portrait(archetype_name, features),
        "metrics": [
            { "value": str(features.get("present_bias_score", 0)), "label": "present bias", "color": "#D4537E" },
            { "value": f"${features.get('total_amount', 0)}", "label": "total analysed", "color": "#2E7D32" },
            { "value": features.get("top_category", ""), "label": "top category", "color": "#FF6B6B" },
        ],
        "insights": insights,
        "chartData": chart_data
    }

def generate_portrait(archetype_name: str, features: dict) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""You are Cipher, a behavioural finance app.
                The user's spending archetype is: {archetype_name}

                Their key behavioural data:
                - Present bias score: {features['present_bias_score']}/100
                - Food delivery ratio: {round(features['food_delivery_ratio'] * 100)}% of food spend
                - Top spending category: {features['top_category']} ({round(features['top_category_dominance'] * 100)}% of total)
                - Subscription density: {round(features['subscription_density'] * 100)}% of transactions
                - Merchant loyalty score: {features['merchant_loyalty']}
                - Comfort score: {features['comfort_score']}/100
                - Status score: {features['status_score']}/100

                Write exactly 2-3 sentences describing their spending psychology. Rules:
                - Be specific to their numbers, not generic
                - Use plain language, not financial jargon
                - Do not be preachy or give advice
                - Speak like a smart friend, not a financial advisor
                - Ground observations in real behavioural science concepts (present bias, loss aversion, etc.)"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    import re, hashlib
    from datetime import datetime

    contents = await file.read()
    
    # check if this PDF was already imported
    file_hash = hashlib.md5(contents).hexdigest()
    db = SessionLocal()
    try:
        existing = db.execute(text("""
            SELECT id FROM imported_files 
            WHERE user_id = :user_id AND file_hash = :file_hash
        """), {"user_id": user_id, "file_hash": file_hash}).fetchone()
        
        if existing:
            return {"error": "This statement has already been imported!"}
        
        transactions = []
        current_year = datetime.now().year
        months = {'JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'}
        
        skip_keywords = [
            'payment', 'sub-total', 'subtotal', 'balance', 'total', 'interest',
            'previous', 'statement', 'date', 'description', 'amount', 'page',
            'citibank', 'mastercard', 'visa', 'giro', 'minimum', 'foreignamount',
            'xxxx', 'miles', 'retail', 'kindly', 'transactionsfor',
            'alltransactions', 'coreg', 'robinson', 'grand', 'pleasenote',
            'ccy', 'conversion', 'bonus', 'carried', 'earned', 'redeemed',
            'protect', 'notify', 'important', 'announcements', 'amtdebited',
            'totalofnew', 'openingbalance', 'closingbalance', 'directdebit',
            'membershipnumber', 'americanexpress', 'krisflyer', 'prepared',
            'creditlimit', 'availablecredit', 'annualrate', 'currentrate',
            'statementperiod', 'creditsummary', 'newcredits', 'newdebits',
        ]

        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if not page_text:
                    continue

                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # skip lines ending in CR (credits/refunds)
                    if line.endswith('CR') or line.endswith('\nCR'):
                        continue

                    line_nospace = line.replace(' ', '').lower()
                    if any(k in line_nospace for k in skip_keywords):
                        continue

                    # ── Pattern 1: Citibank DD MMM e.g. "22MAR GRAB 39.60" ──
                    match1 = re.match(r'^(\d{1,2})([A-Z]{3})\s+(.+)$', line)
                    if match1:
                        day = match1.group(1)
                        mon = match1.group(2)
                        rest = match1.group(3)

                        if mon not in months:
                            continue

                        amt_match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', rest)
                        if not amt_match:
                            continue

                        amount_str = amt_match.group(1)
                        description = rest[:amt_match.start()].strip()
                        description = re.sub(r'\s+(?:Singapore|SINGAPORE)\s*\w*$', '', description).strip()
                        description = re.sub(r'\s+[A-Z]{2,3}$', '', description).strip()
                        description = re.sub(r'\s+\w+\s+(?:SG|MY|IE|US|AU)$', '', description).strip()

                        if not description:
                            continue

                        try:
                            amount = float(amount_str.replace(',', ''))
                            if amount <= 0:
                                continue
                            month_num = datetime.strptime(mon, "%b").month
                            year = current_year if month_num <= datetime.now().month else current_year - 1
                            date_obj = datetime.strptime(f"{day} {mon} {year}", "%d %b %Y")
                            date_formatted = date_obj.strftime("%Y-%m-%d")
                            transactions.append({
                                "description": description,
                                "amount": amount,
                                "category": "",
                                "time": "",
                                "date": date_formatted
                            })
                        except Exception:
                            continue
                        continue

                    # ── Pattern 2: Amex DD.MM.YY e.g. "07.03.26 LOTTE 101.40" ──
                    match2 = re.match(r'^(\d{2})\.(\d{2})\.(\d{2})\s+(.+)$', line)
                    if match2:
                        day = match2.group(1)
                        month_num = int(match2.group(2))
                        year_short = int(match2.group(3))
                        rest = match2.group(4)

                        amt_match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', rest)
                        if not amt_match:
                            continue

                        amount_str = amt_match.group(1)
                        description = rest[:amt_match.start()].strip()
                        description = re.sub(r'\s+SINGAPORE$', '', description).strip()
                        description = re.sub(r'\s+[A-Z]{2,3}$', '', description).strip()

                        if not description:
                            continue

                        try:
                            amount = float(amount_str.replace(',', ''))
                            if amount <= 0:
                                continue
                            full_year = 2000 + year_short
                            date_formatted = f"{full_year}-{str(month_num).zfill(2)}-{day}"
                            transactions.append({
                                "description": description,
                                "amount": amount,
                                "category": "",
                                "time": "",
                                "date": date_formatted
                            })
                        except Exception:
                            continue

        if not transactions:
            return {"error": "No transactions found in PDF"}

        # save file hash so it can't be imported again
        db.execute(text("""
            INSERT INTO imported_files (user_id, file_hash)
            VALUES (:user_id, :file_hash)
        """), {"user_id": user_id, "file_hash": file_hash})
        db.commit()

        return {"transactions": transactions}

    finally:
        db.close()

@app.post("/debug-pdf")
async def debug_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    result = []
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            result.append({"page": i, "text": page_text})
    return {"pages": result}

# ── register endpoint ──
@app.post("/register")
def register(request: RegisterRequest):
    db = SessionLocal()
    try:
        # check if email already exists
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # create new user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(request.password)
        
        db.execute(
            text("INSERT INTO users (id, email, password_hash) VALUES (:id, :email, :password_hash)"),
            {"id": user_id, "email": request.email, "password_hash": password_hash}
        )
        db.commit()
        
        token = create_token(user_id)
        return {"token": token, "user_id": user_id, "email": request.email} # creates JWT and sends it to the frontend
    
    finally:
        db.close()

# ── login endpoint ──
@app.post("/login")
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        # find user by email
        user = db.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_token(user.id)
        return {"token": token, "user_id": user.id, "email": request.email} # creates JWT and send it to the frontend
    
    finally:
        db.close()

# ── transaction endpoints ──
@app.post("/transactions")
def add_transaction(request: dict, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        tx_id = str(uuid.uuid4())
        categorised = categorise_transactions([{
            "description": request.get("description", ""),
            "amount": request.get("amount", 0),
            "category": request.get("category", ""),
            "time": request.get("time", "")
        }])
        
        # if user selected a category, use it; otherwise use ML prediction
        user_category = request.get("category", "")
        predicted = user_category if user_category and user_category != "Others" else (categorised[0]["predicted_category"] if categorised else "")

        db.execute(text("""
            INSERT INTO transactions (id, user_id, description, amount, category, predicted_category, time, date)
            VALUES (:id, :user_id, :description, :amount, :category, :predicted_category, :time, :date)
        """), {
            "id": tx_id,
            "user_id": user_id,
            "description": request.get("description", ""),
            "amount": request.get("amount", 0),
            "category": request.get("category", ""),
            "predicted_category": predicted,
            "time": request.get("time", ""),
            "date": request.get("date", "")
        })
        db.commit()
        return {"success": True, "id": tx_id}
    finally:
        db.close()

@app.get("/transactions")
def get_transactions(month: int = None, year: int = None, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        if month and year:
            rows = db.execute(text("""
                SELECT * FROM transactions 
                WHERE user_id = :user_id AND date LIKE :month
                ORDER BY date DESC
            """), {"user_id": user_id, "month": f"{year}-{str(month).zfill(2)}%"}).fetchall()
        else:
            rows = db.execute(text("""
                SELECT * FROM transactions 
                WHERE user_id = :user_id
                ORDER BY date DESC
            """), {"user_id": user_id}).fetchall()

        transactions = [dict(row._mapping) for row in rows]
        return {"transactions": transactions}
    finally:
        db.close()

@app.post("/transactions/bulk")
def bulk_add_transactions(request: dict, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        txs = request.get("transactions", [])
        categorised = categorise_transactions(txs)

        for tx in categorised:
            tx_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO transactions (id, user_id, description, amount, category, predicted_category, time, date)
                VALUES (:id, :user_id, :description, :amount, :category, :predicted_category, :time, :date)
            """), {
                "id": tx_id,
                "user_id": user_id,
                "description": tx.get("description", ""),
                "amount": tx.get("amount", 0),
                "category": tx.get("category", ""),
                "predicted_category": tx.get("predicted_category", ""),
                "time": tx.get("time", ""),
                "date": tx.get("date", "")
            })
        db.commit()
        return {"success": True, "count": len(categorised)}
    finally:
        db.close()

@app.get("/insights")
def get_insights(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT * FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()

        transactions = [dict(row._mapping) for row in rows]
        count = len(transactions)

        if count < 20:
            return {"unlocked": False, "transaction_count": count}

        # check if cached archetype exists and transaction count hasn't changed
        cached = db.execute(text("""
            SELECT archetype_name, portrait, transaction_count, updated_at 
            FROM archetypes WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()

        import hashlib
        cat_hash = hashlib.md5("".join(sorted(t.get("predicted_category","") for t in transactions)).encode()).hexdigest()[:8]
        if cached and cached.transaction_count == count and (cached.portrait and cat_hash in cached.portrait):
            # return cached version — no Groq call!
            import json
            return json.loads(cached.portrait)

        # generate new archetype
        features = extract_features(transactions)
        archetype_name, archetype_data, scores = assign_archetype(features)
        insights_data = generate_insights(features, archetype_name)
        portrait = generate_portrait(archetype_name, features)

        result = {
            "unlocked": True,
            "transaction_count": count,
            "cat_hash": cat_hash,
            "archetype": archetype_name,
            "portrait": portrait,
            "metrics": [
                {"value": str(features.get("present_bias_score", 0)), "label": "present bias", "color": "#D4537E"},
                {"value": f"${features.get('total_amount', 0)}", "label": "total analysed", "color": "#2E7D32"},
                {"value": features.get("top_category", ""), "label": "top category", "color": "#FF6B6B"},
            ],
            "insights": insights_data
        }

        # save to archetypes table
        import json
        db.execute(text("""
            INSERT INTO archetypes (user_id, archetype_name, portrait, transaction_count)
            VALUES (:user_id, :archetype_name, :portrait, :transaction_count)
            ON CONFLICT (user_id) DO UPDATE SET
                archetype_name = :archetype_name,
                portrait = :portrait,
                transaction_count = :transaction_count,
                updated_at = NOW()
        """), {
            "user_id": user_id,
            "archetype_name": archetype_name,
            "portrait": json.dumps(result),
            "transaction_count": count
        })
        db.commit()

        return result

    finally:
        db.close()

@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM transactions 
            WHERE id = :id AND user_id = :user_id
        """), {"id": tx_id, "user_id": user_id})
        db.commit()
        return {"success": True}
    finally:
        db.close()

@app.put("/transactions/{tx_id}")
def update_transaction(tx_id: str, request: dict, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        # get original category before updating
        original = db.execute(text("""
            SELECT predicted_category FROM transactions 
            WHERE id = :id AND user_id = :user_id
        """), {"id": tx_id, "user_id": user_id}).fetchone()
        original_category = original.predicted_category if original else ""

        categorised = categorise_transactions([{
            "description": request.get("description", ""),
            "amount": request.get("amount", 0),
            "category": request.get("category", ""),
            "time": request.get("time", "")
        }])
        predicted = categorised[0]["predicted_category"] if categorised else ""

        db.execute(text("""
            UPDATE transactions 
            SET description = :description,
                amount = :amount,
                category = :category,
                predicted_category = :predicted_category,
                time = :time,
                date = :date
            WHERE id = :id AND user_id = :user_id
        """), {
            "id": tx_id,
            "user_id": user_id,
            "description": request.get("description", ""),
            "amount": request.get("amount", 0),
            "category": request.get("category", ""),
            "predicted_category": predicted or request.get("category", ""),
            "time": request.get("time", ""),
            "date": request.get("date", "")
        })

        # only save to training queue if category actually changed
        new_category = request.get("category", "")
        if new_category and new_category != original_category:
            db.execute(text("""
                INSERT INTO training_queue (user_id, description, correct_category, original_category)
                VALUES (:user_id, :description, :correct_category, :original_category)
            """), {
                "user_id": user_id,
                "description": request.get("description", ""),
                "correct_category": new_category,
                "original_category": original_category
            })

        db.commit()
        return {"success": True}
    finally:
        db.close()

def _date_prefix(period: str) -> str | None:
    from datetime import date, timedelta
    today = date.today()
    p = period.lower()
    MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
    if p == "last month":
        first = today.replace(day=1)
        last = (first - timedelta(days=1)).replace(day=1)
        return last.strftime("%Y-%m")
    if p == "this month":
        return today.strftime("%Y-%m")
    if p == "this year":
        return str(today.year)
    if p in MONTHS:
        return f"{today.year}-{str(MONTHS[p]).zfill(2)}"
    return None


@app.get("/search")
def search_transactions(category: str, period: str, user_id: str = Depends(get_current_user)):
    from datetime import date
    db = SessionLocal()
    try:
        prefix = _date_prefix(period)
        if prefix:
            rows = db.execute(text("""
                SELECT * FROM transactions
                WHERE user_id = :user_id
                  AND predicted_category = :category
                  AND date LIKE :prefix
                ORDER BY date DESC
            """), {"user_id": user_id, "category": category, "prefix": f"{prefix}%"}).fetchall()
        else:
            rows = db.execute(text("""
                SELECT * FROM transactions
                WHERE user_id = :user_id
                  AND predicted_category = :category
                ORDER BY date DESC
            """), {"user_id": user_id, "category": category}).fetchall()

        transactions = [dict(row._mapping) for row in rows]
        if not transactions:
            return {"answer": f"No {category} transactions found for {period}.", "transactions": []}

        total = sum(tx["amount"] for tx in transactions)
        period_label = period if period not in ("this month", "last month", "this year") else period
        answer = f"You spent ${total:.2f} on {category} {period_label}."
        return {"answer": answer, "transactions": transactions}
    finally:
        db.close()

@app.get("/forecast")
def get_forecast(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try: 
        rows = db.execute(text("""
            SELECT * FROM transactions
            WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchall()
        transactions = [dict(row._mapping) for row in rows]
        
        categories = ["Food", "Groceries", "Transport", "Shopping", "Entertainment", "Health", "Subscriptions", "Utilities"]

        forecasts = []
        for cat in categories:
            result = forecast_next_month(transactions, cat)
            if result["current_spend"] > 0 or result["predicted"] > 0:
                forecasts.append({"category": cat, **result})
        
        return {"forecasts": forecasts} # convention for APIs, makes response extensible 
    finally:
        db.close()