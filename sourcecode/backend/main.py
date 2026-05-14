from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import List
from categoriser import categorise_transactions
from features import extract_features 
from archetypes import assign_archetype, generate_insights

app = FastAPI() # creates FastAPI server 
load_dotenv() # loads .env file 

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
    category: str
    time: str = ""

class AnalyseRequest(BaseModel):
    transactions: List[Transaction]

# ── health check endpoint ──
# when someone hits GET /health, run this fxn
@app.get("/health")
def health():
    return { "status": "ok" }

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
    
    # hardcoded mock response for now
    # real ML pipeline comes later
    return {
        "archetype": archetype_name,
        "portrait": generate_portrait(archetype_name, features),
        "metrics": [
            { "value": str(features.get("present_bias_score", 0)), "label": "present bias", "color": "#D4537E" },
            { "value": f"${features.get('total_amount', 0)}", "label": "total analysed", "color": "#2E7D32" },
            { "value": f"{round(features.get('late_night_ratio', 0) * 100)}%", "label": "late night spend", "color": "#D4537E" },
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
                - Late night spending: {round(features['late_night_ratio'] * 100)}% of transactions
                - Food delivery ratio: {round(features['food_delivery_ratio'] * 100)}% of food spend
                - Top spending category: {features['top_category']} ({round(features['top_category_dominance'] * 100)}% of total)
                - Subscription density: {round(features['subscription_density'] * 100)}% of transactions
                - Merchant loyalty score: {features['merchant_loyalty']}

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