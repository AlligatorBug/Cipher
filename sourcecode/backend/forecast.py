from collections import defaultdict
from datetime import date
import calendar
from sklearn.linear_model import LinearRegression
import numpy as np

def monthly_totals(transactions, category):
    # group transactions by month for this category
    totals = defaultdict(float) # automatically initializes missing keys to 0.0
    for tx in transactions:
        if tx.get("predicted_category") == category: # only consider transactions in the specified category 
            month = tx.get("date", "")[:7]
            if month:
                totals[month] += tx["amount"]
    return dict(sorted(totals.items())) # {"2026-01": 200, "2026-02": 180, ...}

# X = month number (1, 2, 3, 4) — the input
# Y = spending that month (200, 180, 220, 190) — what we're predicting

def forecast_next_month(transactions, category):
    today = date.today()
    current_month = today.strftime("%Y-%m")

    totals = monthly_totals(transactions, category)
    past_months = [value for key, value in totals.items() if key < current_month]
    current_spend = totals.get(current_month, 0.0)

    # pro-rate current month
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    projected = current_spend * (days_in_month / today.day)

    valid_months = [v for v in past_months if isinstance(v, (int, float)) and v >= 0]

    if len(valid_months) < 2:
        predicted = sum(valid_months) / len(valid_months) if valid_months else 0.0
    else:
        X = np.array([[i+1] for i in range(len(valid_months))])
        Y = np.array(valid_months)
        model = LinearRegression()
        model.fit(X, Y)
        raw = model.predict([[len(valid_months) + 1]])[0]
        predicted = float(raw) if np.isfinite(raw) else (sum(valid_months) / len(valid_months))

    return {
        "predicted": round(max(predicted, 0.0), 2),
        "current_spend": round(current_spend, 2),
        "projected": round(projected, 2),
    }