import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import database
from models import *
import ai_service

app = FastAPI(title="Smart Expense Splitter")

# Initialize DB
database.init_db()

# --- API Routes ---

@app.post("/api/users", response_model=UserResponse)
def create_user(user: UserCreate):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", (user.name,))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"id": user_id, "name": user.name}

@app.get("/api/users", response_model=List[UserResponse])
def get_users():
    conn = database.get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [{"id": u["id"], "name": u["name"]} for u in users]

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    conn = database.get_db_connection()
    # Check if user is part of any expenses
    expenses = conn.execute("SELECT * FROM expenses WHERE paid_by = ?", (user_id,)).fetchone()
    splits = conn.execute("SELECT * FROM expense_splits WHERE user_id = ?", (user_id,)).fetchone()
    
    if expenses or splits:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot delete user because they are involved in group expenses.")
        
    cursor = conn.cursor()
    cursor.execute("DELETE FROM group_members WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "User deleted successfully"}


@app.post("/api/groups", response_model=GroupResponse)
def create_group(group: GroupCreate):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO groups (name) VALUES (?)", (group.name,))
    conn.commit()
    group_id = cursor.lastrowid
    
    # fetch the newly created group to get created_at
    g = conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    conn.close()
    return {"id": g["id"], "name": g["name"], "created_at": g["created_at"], "members": []}

@app.get("/api/groups", response_model=List[GroupResponse])
def get_groups():
    conn = database.get_db_connection()
    groups = conn.execute("SELECT * FROM groups").fetchall()
    result = []
    for g in groups:
        members = conn.execute('''
            SELECT u.id, u.name FROM users u
            JOIN group_members gm ON u.id = gm.user_id
            WHERE gm.group_id = ?
        ''', (g["id"],)).fetchall()
        result.append({
            "id": g["id"], 
            "name": g["name"], 
            "created_at": g["created_at"],
            "members": [{"id": m["id"], "name": m["name"]} for m in members]
        })
    conn.close()
    return result

@app.post("/api/groups/{group_id}/members")
def add_group_member(group_id: int, req: AddMemberRequest):
    conn = database.get_db_connection()
    try:
        conn.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, req.user_id))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail="User already in group or invalid IDs")
    conn.close()
    return {"message": "User added to group"}

@app.post("/api/groups/{group_id}/expenses", response_model=ExpenseResponse)
def add_expense(group_id: int, expense: ExpenseCreate):
    conn = database.get_db_connection()
    
    # 1. AI Categorization
    category = ai_service.categorize_expense(expense.description)
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (group_id, description, amount, paid_by, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (group_id, expense.description, expense.amount, expense.paid_by, category))
    expense_id = cursor.lastrowid
    
    splits_data = []
    for split in expense.splits:
        cursor.execute('''
            INSERT INTO expense_splits (expense_id, user_id, amount_owed)
            VALUES (?, ?, ?)
        ''', (expense_id, split.user_id, split.amount_owed))
        splits_data.append({"user_id": split.user_id, "amount_owed": split.amount_owed})
        
    conn.commit()
    
    e = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    
    return {
        "id": e["id"],
        "group_id": e["group_id"],
        "description": e["description"],
        "amount": e["amount"],
        "paid_by": e["paid_by"],
        "category": e["category"],
        "date": e["date"],
        "splits": splits_data
    }

@app.get("/api/groups/{group_id}/expenses")
def get_expenses(group_id: int):
    conn = database.get_db_connection()
    expenses = conn.execute("SELECT * FROM expenses WHERE group_id = ?", (group_id,)).fetchall()
    
    result = []
    for e in expenses:
        splits = conn.execute("SELECT * FROM expense_splits WHERE expense_id = ?", (e["id"],)).fetchall()
        result.append({
            "id": e["id"],
            "description": e["description"],
            "amount": e["amount"],
            "paid_by": e["paid_by"],
            "category": e["category"],
            "date": e["date"],
            "splits": [{"user_id": s["user_id"], "amount_owed": s["amount_owed"]} for s in splits]
        })
    conn.close()
    return result

@app.get("/api/groups/{group_id}/balances")
def get_balances(group_id: int):
    conn = database.get_db_connection()
    
    # Calculate who paid what vs who owes what
    # balances[user_id] = net balance (positive means they are owed money, negative means they owe money)
    balances = {}
    
    members = conn.execute("SELECT user_id FROM group_members WHERE group_id = ?", (group_id,)).fetchall()
    for m in members:
        balances[m["user_id"]] = 0.0
        
    expenses = conn.execute("SELECT * FROM expenses WHERE group_id = ?", (group_id,)).fetchall()
    for e in expenses:
        paid_by = e["paid_by"]
        if paid_by not in balances: balances[paid_by] = 0.0
        balances[paid_by] += e["amount"]
        
        splits = conn.execute("SELECT * FROM expense_splits WHERE expense_id = ?", (e["id"],)).fetchall()
        for s in splits:
            uid = s["user_id"]
            if uid not in balances: balances[uid] = 0.0
            balances[uid] -= s["amount_owed"]
            
    # Settle debts algorithm (Greedy approach)
    debtors = []
    creditors = []
    
    users_info = {u["id"]: u["name"] for u in conn.execute("SELECT * FROM users").fetchall()}
    conn.close()
    
    for uid, bal in balances.items():
        if bal < -0.01:
            debtors.append({"user_id": uid, "name": users_info.get(uid, f"User {uid}"), "amount": -bal})
        elif bal > 0.01:
            creditors.append({"user_id": uid, "name": users_info.get(uid, f"User {uid}"), "amount": bal})
            
    settlements = []
    i = 0
    j = 0
    
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        settle_amount = min(debtor["amount"], creditor["amount"])
        
        settlements.append({
            "from_user": debtor["name"],
            "to_user": creditor["name"],
            "amount": round(settle_amount, 2)
        })
        
        debtor["amount"] -= settle_amount
        creditor["amount"] -= settle_amount
        
        if debtor["amount"] < 0.01: i += 1
        if creditor["amount"] < 0.01: j += 1
        
    return {"balances": {users_info.get(k, k): round(v, 2) for k, v in balances.items()}, "settlements": settlements}


@app.get("/api/groups/{group_id}/insights")
def get_group_insights(group_id: int):
    conn = database.get_db_connection()
    expenses = conn.execute("SELECT description, amount FROM expenses WHERE group_id = ?", (group_id,)).fetchall()
    conn.close()
    
    expenses_list = [{"description": e["description"], "amount": e["amount"]} for e in expenses]
    insight = ai_service.generate_insights(expenses_list)
    return {"insight": insight}

class SettlementMessage(BaseModel):
    message: str

@app.post("/api/ai/suggest_reply")
def suggest_reply(msg: SettlementMessage):
    reply = ai_service.generate_suggested_reply(msg.message)
    return {"reply": reply}

# --- Serve Static Frontend ---

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
