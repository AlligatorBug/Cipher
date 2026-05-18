# test_categoriser.py
# Run with: pytest test_categoriser.py -v

import pytest
from categoriser import categorise_transactions, rule_based_categorise, ml_categorise, clean_description

# ── unit tests for clean_description ──

def test_clean_grab_code():
    """Grab food delivery codes should be normalised to 'grab'"""
    assert 'grab' in clean_description('Grab*A-94HVUOTGWCDSAV')

def test_clean_parking_code():
    """Parking bill IDs should be normalised to 'parking'"""
    assert 'parking' in clean_description('PARKING.SGBILL_B5FA68')

def test_clean_lowercase():
    """Output should always be lowercase"""
    result = clean_description('JUNGYIKOREANBBQ')
    assert result == result.lower()

def test_clean_removes_numbers():
    """Numbers should be removed"""
    result = clean_description('M1 LIMITED 12345')
    assert '12345' not in result

# ── unit tests for rule_based_categorise ──

def test_rule_transport_parking():
    assert rule_based_categorise('PARKING.SGBILL_B5FA68') == 'Transport'

def test_rule_transport_mrt():
    assert rule_based_categorise('BUS/MRT808762699') == 'Transport'

def test_rule_groceries_ntuc():
    assert rule_based_categorise('NTUC FAIRPRICE APP PAYM') == 'Groceries'

def test_rule_groceries_fairprice():
    assert rule_based_categorise('FAIRPRICE APP VIVO FAIR') == 'Groceries'

def test_rule_subscriptions_netflix():
    assert rule_based_categorise('NETFLIX SINGAPORE') == 'Subscriptions'

def test_rule_subscriptions_spotify():
    assert rule_based_categorise('SPOTIFY PREMIUM SG') == 'Subscriptions'

def test_rule_utilities_sp():
    assert rule_based_categorise('SP DIGITAL PTE. LTD.') == 'Utilities'

def test_rule_utilities_cnergy():
    assert rule_based_categorise('UNION GAS CNERGY - DUNM') == 'Utilities'

def test_rule_health_watsons():
    assert rule_based_categorise("WATSON'S PERSONAL CARE") == 'Health'

def test_rule_no_match_returns_none():
    assert rule_based_categorise('XYZUNKNOWNMERCHANT123') is None

# ── unit tests for ml_categorise ──

def test_ml_grab_food():
    pred, conf = ml_categorise('Grab*A-94HVUOTGWCDSAV')
    assert pred == 'Food'
    assert conf > 0.25

def test_ml_parking():
    pred, conf = ml_categorise('PARKING.SGBILL_NEWCODE')
    assert pred == 'Transport'
    assert conf > 0.25

def test_ml_korean_bbq():
    pred, conf = ml_categorise('JUNGYIKOREANBBQ')
    assert pred == 'Food'

def test_ml_health():
    pred, conf = ml_categorise('BFITHEALTH')
    assert pred == 'Health'

def test_ml_shopping():
    pred, conf = ml_categorise('DAISOJAPAN-EPM')
    assert pred == 'Shopping'

def test_ml_returns_tuple():
    result = ml_categorise('ANYMERCHANT')
    assert isinstance(result, tuple)
    assert len(result) == 2

# ── integration tests for categorise_transactions ──

def test_categorise_single_transaction():
    txs = [{"description": "JUNGYIKOREANBBQ", "amount": 54.0, "category": "", "time": ""}]
    result = categorise_transactions(txs)
    assert len(result) == 1
    assert result[0]["predicted_category"] == "Food"

def test_categorise_respects_user_category():
    """If user explicitly set a category, it should be respected"""
    txs = [{"description": "JUNGYIKOREANBBQ", "amount": 54.0, "category": "Health", "time": ""}]
    result = categorise_transactions(txs)
    assert result[0]["predicted_category"] == "Health"

def test_categorise_ignores_others_user_category():
    """If user set 'Others', ML should still try to categorise"""
    txs = [{"description": "NTUC FAIRPRICE APP PAYM", "amount": 44.45, "category": "Others", "time": ""}]
    result = categorise_transactions(txs)
    assert result[0]["predicted_category"] == "Groceries"

def test_categorise_bulk():
    txs = [
        {"description": "GRAB*A-94HVUOTGWCDSAV", "amount": 39.60, "category": "", "time": ""},
        {"description": "NTUC FAIRPRICE APP PAYM", "amount": 44.45, "category": "", "time": ""},
        {"description": "PARKING.SGBILL_B5FA68", "amount": 0.26, "category": "", "time": ""},
        {"description": "SP DIGITAL PTE. LTD.", "amount": 202.18, "category": "", "time": ""},
        {"description": "NETFLIX SINGAPORE", "amount": 15.98, "category": "", "time": ""},
    ]
    result = categorise_transactions(txs)
    assert result[0]["predicted_category"] == "Food"
    assert result[1]["predicted_category"] == "Groceries"
    assert result[2]["predicted_category"] == "Transport"
    assert result[3]["predicted_category"] == "Utilities"
    assert result[4]["predicted_category"] == "Subscriptions"

def test_categorise_preserves_original_fields():
    """categorise_transactions should not lose any original fields"""
    txs = [{"description": "GRAB FOOD", "amount": 18.50, "category": "", "time": "", "date": "2026-03-22"}]
    result = categorise_transactions(txs)
    assert result[0]["description"] == "GRAB FOOD"
    assert result[0]["amount"] == 18.50
    assert result[0]["date"] == "2026-03-22"
    assert "predicted_category" in result[0]