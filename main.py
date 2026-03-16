from fastmcp import FastMCP
import aiosqlite
import uuid
from datetime import datetime
import os

# Initialize MCP server
mcp = FastMCP("Expense Tracker MCP Server")


# -------------------------
# DATABASE HELPER
# -------------------------
async def get_db(user_id: str):

    db = await aiosqlite.connect(f"expenses_{user_id}.db")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT
        )
    """)

    await db.commit()
    return db


# -------------------------
# USER REGISTRATION
# -------------------------
@mcp.tool()
async def register_user(name: str):
    """Register new user"""

    user_id = str(uuid.uuid4())

    return {
        "user_id": user_id,
        "message": f"User {name} registered successfully"
    }


# -------------------------
# ADD EXPENSE
# -------------------------
@mcp.tool()
async def add_expense(
    user_id: str,
    amount: float,
    category: str,
    description: str
):
    """Add a new expense"""

    if amount <= 0:
        return {"error": "Amount must be greater than 0"}

    db = await get_db(user_id)

    date = datetime.now().strftime("%Y-%m-%d")

    await db.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (amount, category, description, date)
    )

    await db.commit()
    await db.close()

    return {
        "status": "success",
        "message": "Expense added"
    }


# -------------------------
# LIST EXPENSES
# -------------------------
@mcp.tool()
async def list_expenses(user_id: str):
    """List all expenses"""

    db = await get_db(user_id)

    cursor = await db.execute("""
        SELECT id, amount, category, description, date
        FROM expenses
        ORDER BY date DESC
    """)

    rows = await cursor.fetchall()

    await db.close()

    return rows


# -------------------------
# UPDATE EXPENSE
# -------------------------
@mcp.tool()
async def update_expense(
    user_id: str,
    expense_id: int,
    amount: float,
    category: str,
    description: str
):
    """Update an expense"""

    db = await get_db(user_id)

    await db.execute("""
        UPDATE expenses
        SET amount=?, category=?, description=?
        WHERE id=?
    """, (amount, category, description, expense_id))

    await db.commit()
    await db.close()

    return {
        "status": "updated",
        "expense_id": expense_id
    }


# -------------------------
# DELETE EXPENSE
# -------------------------
@mcp.tool()
async def delete_expense(user_id: str, expense_id: int):
    """Delete an expense"""

    db = await get_db(user_id)

    await db.execute(
        "DELETE FROM expenses WHERE id=?",
        (expense_id,)
    )

    await db.commit()
    await db.close()

    return {
        "status": "deleted",
        "expense_id": expense_id
    }


# -------------------------
# TOTAL SPENDING
# -------------------------
@mcp.tool()
async def total_spent(user_id: str):
    """Total money spent"""

    db = await get_db(user_id)

    cursor = await db.execute(
        "SELECT SUM(amount) FROM expenses"
    )

    result = await cursor.fetchone()

    await db.close()

    return result[0] if result[0] else 0


# -------------------------
# CATEGORY SUMMARY
# -------------------------
@mcp.tool()
async def category_summary(user_id: str):
    """Total spending per category"""

    db = await get_db(user_id)

    cursor = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        GROUP BY category
    """)

    rows = await cursor.fetchall()

    await db.close()

    return rows


# -------------------------
# MONTHLY REPORT
# -------------------------
@mcp.tool()
async def monthly_report(user_id: str, month: str):
    """
    Monthly report
    month format: YYYY-MM
    """

    db = await get_db(user_id)

    cursor = await db.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
    """, (f"{month}%",))

    rows = await cursor.fetchall()

    await db.close()

    return rows


# -------------------------
# CLEAR ALL EXPENSES
# -------------------------
@mcp.tool()
async def clear_expenses(user_id: str):
    """Delete all expenses"""

    db = await get_db(user_id)

    await db.execute("DELETE FROM expenses")

    await db.commit()
    await db.close()

    return {"status": "all expenses deleted"}


# -------------------------
# START SERVER
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )