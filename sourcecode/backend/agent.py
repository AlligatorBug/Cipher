from database import SessionLocal
from sqlalchemy import text
from main import _date_prefix
import sqlparse
import os

# for llm to understand the schema hehe
SCHEMA = """
Table: transactions
Columns:
    - id (uuid, primary key)
    - user_id (text) — always filter by this, never omit it
    - description (text) — merchant name e.g. "GRAB", "FAIRPRICE"
    - amount (float) — always positive, in SGD
    - category (text) — user-assigned category
    - predicted_category (text) — ML-assigned, use this one for analysis
    - date (text, format YYYY-MM-DD)
Categories in use: Food, Groceries, Transport, Shopping, Entertainment, Health, Subscriptions, Utilities, Others
"""

# query the database with provided SQL string
def query_database(sql: str, user_id: str) -> str:
    parsed = sqlparse.parse(sql)
    if not all(s.get_type() == "SELECT" for s in parsed):
        return "Error: only SELECT queries are allowed"

    db = SessionLocal()
    try:
        result = db.execute(text(sql), {"user_id": user_id})
        rows = result.fetchall()
        if not rows:
            return "No results found."
        return str([dict(row._mapping) for row in rows]) # convert result rows to dicts
    except Exception as e:
        return f"Query error: {str(e)}"
    finally:
        db.close()

def get_spending_summary(period: str, user_id: str) -> str:
    prefix = _date_prefix(period)
    db = SessionLocal()
    try:
        if prefix:
            rows = db.execute(text("""
                SELECT predicted_category, COUNT(*) as count, ROUND(SUM(amount)::numeric, 2) as total
                FROM transactions
                WHERE user_id = :user_id AND date LIKE :prefix
                GROUP BY predicted_category
                ORDER BY total DESC
            """), {"user_id": user_id, "prefix": f"{prefix}%"}).fetchall()
        else:
            return f"Sorry, I don't understand the period '{period}'. Try 'May', 'last month', or 'this month'."
        
        if not rows:
            return f"No transactions found for {period}."
        
        summary = [dict(row._mapping) for row in rows]
        total_spent = sum(r["total"] for r in summary)
        return f"Spending summary for {period} (total: ${total_spent:.2f}):\n" + \
                "\n".join(f"{r['predicted_category']}: ${r['total']} ({r['count']} transactions)" for r in summary)
    finally:
        db.close()

def explain_anomaly(transaction_id: str, user_id: str) -> str:
    db = SessionLocal()
    try:
        tx = db.execute(text("""
            SELECT * FROM transactions
            WHERE id = :transaction_id AND user_id = :user_id
        """), {"transaction_id": transaction_id, "user_id": user_id}).fetchone()

        if not tx:
            return "Transaction not found."

        tx = dict(tx._mapping)

        # category stats to compare against
        stats = db.execute(text("""
            SELECT COUNT(*) as count,
                   ROUND(AVG(amount)::numeric, 2) as avg_amount,
                   ROUND(MAX(amount)::numeric, 2) as max_amount
            FROM transactions
            WHERE user_id = :user_id AND predicted_category = :category
        """), {"user_id": user_id, "category": tx["predicted_category"]}).fetchone()


        stats = dict(stats._mapping)

        return (
            f"Transaction: {tx['description']} - ${tx['amount']} on {tx['date']}\n"
            f"Category: {tx['predicted_category']}\n"
            f"Your average for this category: ${stats['avg_amount']} "
            f"(across {stats['count']} transactions, max ever: ${stats['max_amount']})\n"
            f"This transaction is {round(tx['amount'] / float(stats['avg_amount']), 1)}x your usual spend."
        )
    finally:
        db.close()

if __name__ == "__main__":
    test_user_id = "ce6fe333-f788-46ca-9a80-4784fae2df6e"
    
    print("=== query_database ===")
    print(query_database(
        "SELECT description, amount, date FROM transactions WHERE user_id = :user_id ORDER BY date DESC LIMIT 5",
        test_user_id
    ))
    
    print("\n=== get_spending_summary ===")
    print(get_spending_summary("last month", test_user_id))
    
    print("\n=== explain_anomaly ===")
    # grab a real transaction id from the query above and paste it here
    print(explain_anomaly("04561458-93ad-45e7-83fe-71962615a63e", test_user_id))
