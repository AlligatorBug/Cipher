from database import SessionLocal
from sqlalchemy import text
from main import _date_prefix
from langchain.agents import create_agent as lc_create_agent # runs the agent loop: think->call tool->think->call tool->answer
from langchain_openai import ChatOpenAI # LLM 
from langchain_core.tools import tool # wrap python fxns into smt langchain understands 
from langchain_core.prompts import ChatPromptTemplate # structures the system prompt + convo history
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

# system prompt to LLM
SYSTEM_PROMPT = """
You are CipherAgent, a personal finance assistant with access to the user's real transaction data.
You have access to these tools:
- query_database: run a custom SQL SELECT query against the transactions table
- get_spending_summary: get a category breakdown for a time period (e.g. "last month", "May")
- explain_anomaly: get context around a specific transaction ID
- get_monthly_trend: month-by-month spending trend for a category
- search_merchant: search transactions by merchant name
- get_anomalies: list all unusual or suspicious transactions
- get_archetype: get the user's spending personality type
- get_forecast: predicted spending for next month by category

Schema: {schema}
Rules:
- Always use get_spending_summary first for period-based questions before drilling into specifics
- Always filter by user_id in any SQL you write (it's already handled for you)
- Be specific and reference real numbers from the data
- Speak like a smart friend, not a financial advisor
""".format(schema=SCHEMA)

"""
below are the tools that are provided for CipherAgent to use :-) 
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

# get spending summary :-)
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

# get anomalies 
def get_anomalies(user_id: str) -> str:
    from anomaly import detect_anomalies

    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT * FROM transactions WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchall()

        transactions = [dict(row._mapping) for row in rows]

        if len(transactions) < 10:
            return "Not enough transactions to detect anomalies yet (need at least 10)."

        anomalies = detect_anomalies(transactions)
        if not anomalies:
            return "No unusual spending detected."
        
        lines = [
            f"{a['date']} — {a['description']}: ${a['amount']} ({a['severity']} severity)\n  Reason: {a['reason']}"
            for a in anomalies
        ]
        return f"Found {len(anomalies)} unusual transactions:\n\n" + "\n\n".join(lines)
    finally:
        db.close()

# answer anomaly related qns
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

# access forecast data 
def get_forecast(user_id: str) -> str:
    from forecast import forecast_next_month

    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT * FROM transactions WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchall()

        transactions = [dict(row._mapping) for row in rows]

        if not transactions:
            return "No transactions found to forecast from."

        categories = ["Food", "Groceries", "Transport", "Shopping", "Entertainment", "Health", "Subscriptions", "Utilities"]
        lines = []
        for cat in categories:
            result = forecast_next_month(transactions, cat)
            if result["current_spend"] > 0 or result["predicted"] > 0:
                lines.append(f"{cat}: predicted ${result['predicted']:.2f} next month (currently ${result['current_spend']:.2f} this month)")

        if not lines:
            return "Not enough data to generate a forecast yet."

        return "Spending forecast for next month:\n" + "\n".join(lines)
    finally:
        db.close()

# access archetype hehe
def get_archetype(user_id: str) -> str:
    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT archetype_name, transaction_count, updated_at
            FROM archetypes WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()

        if not row:
            return "No archetype found yet. The user needs at least 20 transactions to unlock their spending archetype."
        
        row = dict(row._mapping)
        return (
            f"Spending archetype: {row['archetype_name']}\n"
            f"Based on {row['transaction_count']} transactions, last updated {row['updated_at']}"
        )
    finally:
        db.close()

# searches spending by merchant name 
def search_merchant(merchant: str, user_id: str) -> str:
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT description, amount, date, predicted_category
            FROM transactions
            WHERE user_id = :user_id AND description ILIKE :merchant
            ORDER BY date DESC
        """), {"user_id": user_id, "merchant": f"%{merchant}%"}).fetchall()

        if not rows:
            return f"No transactions found for merchant: {merchant}"
        
        result = [dict(row._mapping) for row in rows]
        total = sum(r["amount"] for r in result)
        lines = [f"{r['date']} — {r['description']}: ${r['amount']}" for r in result]
        return f"Found {len(result)} transactions at '{merchant}' totalling ${total:.2f}:\n" + "\n".join(lines)
    finally:
        db.close()

# monthly trends 
def get_monthly_trend(category: str, user_id: str) -> str:
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT TO_CHAR(date::date, 'YYYY-MM') as month,
                               COUNT(*) as count,
                               ROUND(SUM(amount)::numeric,2) as total
            FROM transactions
            WHERE user_id = :user_id AND predicted_category = :category
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """), {"user_id": user_id, "category": category}).fetchall()

        if not rows:
            return f"No transactions found for category: {category}"
        
        result = [dict(row._mapping) for row in rows]
        lines = [f"{r['month']}: ${r['total']} ({r['count']} transactions)" for r in result]
        return f"Monthly trend for {category} (last 6 months):\n" + "\n".join(lines)
    finally:
        db.close()


# tool wrappers :-) for langchain to access
# name = what LLM calls it by (name of fxn)
# description = plain english telling LLM when to use it
# func = actual Python fxns to run
def make_tools(user_id: str):
    @tool
    def query_database_tool(sql: str) -> str:
        """Run a SELECT SQL query on the transactions table. Use :user_id in WHERE clause for user filtering — it's handled automatically."""
        return query_database(sql, user_id)

    @tool
    def get_spending_summary_tool(period: str) -> str:
        """Get spending breakdown by category for a period. Period can be 'last month', 'this month', 'this year', or a month name like 'May'."""
        return get_spending_summary(period, user_id)

    @tool
    def get_anomalies_tool():
        """Get a list of all unusual or suspicious transactions. Use for questions like 'any weird spending?' or 'what should I look into?'."""
        return get_anomalies(user_id)

    @tool
    def explain_anomaly_tool(transaction_id: str) -> str:
        """Get context around a specific transaction to explain why it looks unusual. Pass the transaction ID."""
        return explain_anomaly(transaction_id, user_id)

    @tool
    def get_monthly_trend_tool(category: str) -> str:
        """Get month-by-month spending trend for a category over the last 6 months. Use for questions like 'is my food spend going up?' or 'show me my transport trend'."""
        return get_monthly_trend(category, user_id)

    @tool
    def search_merchant_tool(merchant: str) -> str:
        """Search all transactions by merchant name. Use for questions like 'how much have I spent at Grab?' or 'show me all my McDonald's transactions'."""
        return search_merchant(merchant, user_id)

    @tool
    def get_archetype_tool() -> str:
        """Get the user's spending archetype and personality type. Use for questions like 'what kind of spender am I?' or 'what's my spending personality?'."""
        return get_archetype(user_id)
    
    @tool
    def get_forecast_tool() -> str:
        """Get predicted spending for next month by category. Use for questions like 'what will I spend next month?' or 'forecast my spending'."""
        return get_forecast(user_id)
    

    return [query_database_tool, get_spending_summary_tool, get_anomalies_tool, explain_anomaly_tool,
            get_monthly_trend_tool, search_merchant_tool, get_archetype_tool, get_forecast_tool]

# langchain wrapper around the OpenAI API so it knows how to work with tools, handle the agent loop and pass the scratchpad back and forth etc
def create_agent(user_id: str):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0, # makes LLM deterministic, no creativity, just reasoning -> want this for data agent
        api_key=os.getenv("OPENAI_API_KEY")
    )

    tools = make_tools(user_id)

    return lc_create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

if __name__ == "__main__":
    test_user_id = "ce6fe333-f788-46ca-9a80-4784fae2df6e"

    agent = create_agent(test_user_id)

    questions = [
        "how much did i spend last month and what was my biggest category?",
        "what are my 3 most expensive transactions ever?",
        "do i have any unusual spending i should know about?",
        "what kind of spender am i?",
        "is my food spending going up or down?",
        "how much have i spent on singapore airlines?",
        "what should i expect to spend next month?",
        "any weird spending i should know about?",
    ]

    for q in questions:
        print(f"Q:{q}")
        result = agent.invoke({"messages": [{"role": "user", "content": q}]})
        print(result["messages"][-1].content)