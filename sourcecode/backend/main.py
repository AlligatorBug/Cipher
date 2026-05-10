from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from categoriser import categorise_transactions
from features import extract_features 
from archetypes import assign_archetype, generate_insights

app = FastAPI() # creates FastAPI server 

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
        "portrait": archetype_data["description"],
        "metrics": [
            { "value": str(features.get("present_bias_score", 0)), "label": "present bias", "color": "#D4537E" },
            { "value": f"${features.get('total_amount', 0)}", "label": "total analysed", "color": "#2E7D32" },
            { "value": f"{round(features.get('late_night_ratio', 0) * 100)}%", "label": "late night spend", "color": "#D4537E" },
        ],
        "insights": insights,
        "chartData": chart_data
    }