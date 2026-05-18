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