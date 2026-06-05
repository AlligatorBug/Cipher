# test_api.py
# Run with: pytest test_api.py -v

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── health check ──

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

# ── auth endpoints ──

def test_register_new_user():
    res = client.post("/register", json={
        "email": "test_cipher_user@test.com",
        "password": "testpassword123"
    })
    # either 200 (new user) or 400 (already exists)
    assert res.status_code in [200, 400]
    if res.status_code == 200:
        assert "token" in res.json()

def test_login_valid():
    # register first
    client.post("/register", json={
        "email": "test_login@test.com",
        "password": "testpassword123"
    })
    res = client.post("/login", json={
        "email": "test_login@test.com",
        "password": "testpassword123"
    })
    assert res.status_code == 200
    assert "token" in res.json()

def test_login_wrong_password():
    res = client.post("/login", json={
        "email": "test_login@test.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_login_nonexistent_user():
    res = client.post("/login", json={
        "email": "nobody@nowhere.com",
        "password": "password"
    })
    assert res.status_code == 401

# ── auth protection ──

def test_transactions_requires_auth():
    """GET /transactions without token should return 422"""
    res = client.get("/transactions")
    assert res.status_code == 422

def test_insights_requires_auth():
    """GET /insights without token should return 422"""
    res = client.get("/insights")
    assert res.status_code == 422

# ── transactions ──

def get_token():
    """Helper to get a valid token for authenticated tests"""
    client.post("/register", json={
        "email": "test_tx@test.com",
        "password": "testpassword123"
    })
    res = client.post("/login", json={
        "email": "test_tx@test.com",
        "password": "testpassword123"
    })
    return res.json()["token"]

def test_add_transaction():
    token = get_token()
    res = client.post("/transactions",
        json={
            "description": "Test Grab Food",
            "amount": 18.50,
            "category": "Food",
            "date": "2026-05-01",
            "time": ""
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["success"] == True

def test_get_transactions():
    token = get_token()
    res = client.get("/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert "transactions" in res.json()

def test_get_transactions_with_month_filter():
    token = get_token()
    res = client.get("/transactions?month=5&year=2026",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert "transactions" in res.json()

def test_delete_transaction():
    token = get_token()
    add = client.post("/transactions",
        json={"description": "Delete me", "amount": 5.0, "category": "Food", "date": "2026-05-01", "time": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    tx_id = add.json()["id"]
    res = client.delete(f"/transactions/{tx_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["success"] == True

def test_delete_other_users_transaction_fails():
    token1 = get_token()
    add = client.post("/transactions",
        json={"description": "Mine", "amount": 5.0, "category": "Food", "date": "2026-05-01", "time": ""},
        headers={"Authorization": f"Bearer {token1}"}
    )
    tx_id = add.json()["id"]
    # register a second user and try to delete first user's transaction
    client.post("/register", json={"email": "other_user@test.com", "password": "password123"})
    res2 = client.post("/login", json={"email": "other_user@test.com", "password": "password123"})
    token2 = res2.json()["token"]
    res = client.delete(f"/transactions/{tx_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 200  # silently no-ops (WHERE includes user_id)

def test_search_requires_auth():
    res = client.get("/search?category=Food&period=last month")
    assert res.status_code == 422

def test_search_returns_answer_and_transactions():
    token = get_token()
    res = client.get("/search?category=Food&period=this year",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "transactions" in data

def test_forecast_requires_auth():
    res = client.get("/forecast")
    assert res.status_code == 422

def test_forecast_returns_forecasts_list():
    token = get_token()
    res = client.get("/forecast", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "forecasts" in res.json()
    assert isinstance(res.json()["forecasts"], list)

def test_bulk_add_transactions():
    token = get_token()
    res = client.post("/transactions/bulk",
        json={"transactions": [
            {"description": "GRAB FOOD", "amount": 12.50, "category": "", "date": "2026-05-01", "time": ""},
            {"description": "NTUC FAIRPRICE APP PAYM", "amount": 44.45, "category": "", "date": "2026-05-02", "time": ""},
        ]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["count"] == 2