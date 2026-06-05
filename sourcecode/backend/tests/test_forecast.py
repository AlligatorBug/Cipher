# test_forecast.py
# Run with: pytest test_forecast.py -v

import pytest
from forecast import monthly_totals, forecast_next_month

FOOD_TXS = [
    {"predicted_category": "Food", "amount": 200.0, "date": "2026-01-15"},
    {"predicted_category": "Food", "amount": 180.0, "date": "2026-02-10"},
    {"predicted_category": "Food", "amount": 220.0, "date": "2026-03-22"},
    {"predicted_category": "Food", "amount": 190.0, "date": "2026-04-05"},
    {"predicted_category": "Groceries", "amount": 80.0, "date": "2026-01-20"},
]

# ── monthly_totals ──

def test_monthly_totals_groups_by_month():
    result = monthly_totals(FOOD_TXS, "Food")
    assert result == {"2026-01": 200.0, "2026-02": 180.0, "2026-03": 220.0, "2026-04": 190.0}

def test_monthly_totals_ignores_other_categories():
    result = monthly_totals(FOOD_TXS, "Food")
    assert "Groceries" not in str(result)
    assert 80.0 not in result.values()

def test_monthly_totals_sums_same_month():
    txs = [
        {"predicted_category": "Food", "amount": 12.50, "date": "2026-01-01"},
        {"predicted_category": "Food", "amount": 8.00, "date": "2026-01-15"},
        {"predicted_category": "Food", "amount": 5.00, "date": "2026-01-28"},
    ]
    result = monthly_totals(txs, "Food")
    assert result["2026-01"] == pytest.approx(25.50)

def test_monthly_totals_empty_transactions():
    assert monthly_totals([], "Food") == {}

def test_monthly_totals_no_matching_category():
    assert monthly_totals(FOOD_TXS, "Entertainment") == {}

def test_monthly_totals_sorted_chronologically():
    keys = list(monthly_totals(FOOD_TXS, "Food").keys())
    assert keys == sorted(keys)

# ── forecast_next_month ──

def test_forecast_returns_required_keys():
    result = forecast_next_month(FOOD_TXS, "Food")
    assert "predicted" in result
    assert "current_spend" in result
    assert "projected" in result

def test_forecast_predicted_non_negative():
    result = forecast_next_month(FOOD_TXS, "Food")
    assert result["predicted"] >= 0.0

def test_forecast_cold_start_one_month():
    txs = [{"predicted_category": "Food", "amount": 150.0, "date": "2026-01-10"}]
    result = forecast_next_month(txs, "Food")
    assert result["predicted"] == pytest.approx(150.0)

def test_forecast_cold_start_no_history():
    result = forecast_next_month([], "Food")
    assert result["predicted"] == 0.0
    assert result["current_spend"] == 0.0
    assert result["projected"] == 0.0

def test_forecast_cold_start_wrong_category():
    result = forecast_next_month(FOOD_TXS, "Entertainment")
    assert result["predicted"] == 0.0

def test_forecast_predicted_is_float():
    result = forecast_next_month(FOOD_TXS, "Food")
    assert isinstance(result["predicted"], float)

def test_forecast_current_spend_zero_if_no_june_txs():
    # FOOD_TXS only goes up to April, so current spend for June should be 0
    result = forecast_next_month(FOOD_TXS, "Food")
    assert result["current_spend"] == 0.0

def test_forecast_projected_zero_if_no_current_spend():
    result = forecast_next_month(FOOD_TXS, "Food")
    assert result["projected"] == 0.0
