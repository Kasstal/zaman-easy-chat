# app/infrastructure/chatbot/services/tools_impl.py
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.infrastructure.services.rag_service import rag
from app.infrastructure.sqlite_repository import DatabaseManager

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_db = DatabaseManager()

def _ensure_aux_tables() -> None:
    with _db.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                user_id TEXT NOT NULL,
                month TEXT NOT NULL,                -- 'YYYY-MM-01'
                category TEXT NOT NULL,
                amount_kzt REAL NOT NULL,           -- ✅ store KZT major units
                PRIMARY KEY (user_id, month, category)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credit_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT,
                amount_kzt REAL NOT NULL,           -- ✅ KZT major
                term_months INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposit_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT,
                initial_deposit_kzt REAL NOT NULL,  -- ✅ KZT major
                term_months INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
_ensure_aux_tables()

def _now_iso() -> str:
    return datetime.utcnow().isoformat()

def _ensure_user_row(conn, user_id: str) -> None:
    row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        return
    conn.execute("""
        INSERT INTO users (id, email, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, f"{user_id}@placeholder.local", "User", "Unknown", _now_iso()))

def _last_months_range(months: int = 6) -> Tuple[str, str]:
    end = datetime.utcnow().date()
    start = (end - timedelta(days=30*months))
    return (start.isoformat(), end.isoformat())

def _read_income_kzt(conn, user_id: str) -> Optional[float]:
    row = conn.execute("SELECT monthly_income FROM users WHERE id = ?", (user_id,)).fetchone()
    return float(row["monthly_income"]) if row and row["monthly_income"] is not None else None

def _write_income_kzt(conn, user_id: str, income_monthly_kzt: float) -> None:
    _ensure_user_row(conn, user_id)
    conn.execute(
        "UPDATE users SET monthly_income = ? WHERE id = ?",
        (float(income_monthly_kzt), user_id)
    )

def _fetch_recent_expenses_kzt(conn, user_id: str, months: int = 6) -> List[Dict[str, Any]]:
    start, end = _last_months_range(months)
    rows = conn.execute("""
        SELECT amount, category, description, transaction_date
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'expense'
          AND transaction_date BETWEEN ? AND ?
    """, (user_id, start, end)).fetchall()

    return [{
        "type": "EXPENSE",
        "category": r["category"] or "other",
        "amount_kzt": float(r["amount"] or 0.0),
        "description": r["description"],
        "date": r["transaction_date"],
    } for r in rows]

def _baseline_monthly_expense_kzt(conn, user_id: str, months: int = 6) -> float:
    txns = _fetch_recent_expenses_kzt(conn, user_id, months)
    total = sum(t["amount_kzt"] for t in txns)
    return round(total / max(1, months), 2)

def _read_goals(conn, user_id: str) -> List[Dict[str, Any]]:
    rows = conn.execute("""
        SELECT id, title, description, goal_type, target_amount, current_amount, target_date, status
        FROM goals WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    goals = []
    for r in rows:
        monthly_contrib_kzt = None
        if r["description"]:
            try:
                d = json.loads(r["description"])
                monthly_contrib_kzt = d.get("monthly_contribution_kzt")
            except Exception:
                pass
        goals.append({
            "id": r["id"],
            "name": r["title"],
            "goal_type": r["goal_type"],
            "target_kzt": float(r["target_amount"] or 0.0),   # stored as REAL
            "current_kzt": float(r["current_amount"] or 0.0), # stored as REAL
            "due_date": r["target_date"],
            "status": r["status"],
            "monthly_contribution_kzt": monthly_contrib_kzt
        })
    return goals

# -------------------- Public tools (KZT majors) --------------------

def get_snapshot(user_id: str) -> Dict[str, Any]:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        income_kzt = _read_income_kzt(conn, user_id)
        txns = _fetch_recent_expenses_kzt(conn, user_id, months=6)
        goals = _read_goals(conn, user_id)

        rows = conn.execute(
            "SELECT month, category, amount_kzt FROM budgets WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        budgets: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            budgets.setdefault(r["month"], []).append({
                "category": r["category"],
                "amount_kzt": float(r["amount_kzt"])
            })

        return {
            "user_id": user_id,
            "income_monthly_kzt": income_kzt,     # ✅ KZT major units
            "transactions": txns,                 # uses amount_kzt
            "goals": goals,
            "budgets": budgets
        }

def upsert_income(user_id: str, income_monthly_kzt: float) -> bool:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        _write_income_kzt(conn, user_id, float(income_monthly_kzt))
        log.info(f"[UpsertIncome] user_id={user_id}, income_kzt={income_monthly_kzt}")
        return True

def upsert_budget(user_id: str, month: str, items: List[Dict[str, Any]]) -> bool:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        conn.execute("DELETE FROM budgets WHERE user_id = ? AND month = ?", (user_id, month))
        for it in items:
            conn.execute("""
                INSERT INTO budgets (user_id, month, category, amount_kzt)
                VALUES (?, ?, ?, ?)
            """, (user_id, month, str(it["category"]), float(it["amount_kzt"])))
        log.info(f"[UpsertBudget] user_id={user_id}, month={month}, items={len(items)}")
        return True

def update_budget_category(user_id: str, month: str, category: str, amount_kzt: float) -> bool:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        conn.execute("""
            INSERT INTO budgets (user_id, month, category, amount_kzt)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, month, category) DO UPDATE SET amount_kzt=excluded.amount_kzt
        """, (user_id, month, category, float(amount_kzt)))
        log.info(f"[UpdateBudgetCategory] user_id={user_id}, month={month}, category={category}, amount_kzt={amount_kzt}")
        return True

def update_goal(
    user_id: str,
    goal_id: Optional[str] = None,
    name: Optional[str] = None,
    monthly_contribution_kzt: Optional[float] = None,
    target_kzt: Optional[float] = None,
    due_date: Optional[str] = None,
    months: Optional[int] = None,   # ✅ NEW
    status: Optional[str] = None,
    **_
) -> bool:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)

        # ✅ Auto-compute monthly contribution if not provided but months+target are known
        if monthly_contribution_kzt is None and target_kzt is not None and months and months > 0:
            monthly_contribution_kzt = round(float(target_kzt) / months, 2)

        if goal_id:
            row = conn.execute(
                "SELECT id, description FROM goals WHERE id = ? AND user_id = ?",
                (goal_id, user_id)
            ).fetchone()
            if row:
                desc_obj = {}
                if row["description"]:
                    try:
                        desc_obj = json.loads(row["description"]) or {}
                    except Exception:
                        desc_obj = {"_raw": row["description"]}

                if monthly_contribution_kzt is not None:
                    desc_obj["monthly_contribution_kzt"] = float(monthly_contribution_kzt)
                if months is not None:
                    desc_obj["months"] = int(months)  # keep months info for reference

                updates, params = [], []
                if name is not None:
                    updates.append("title = ?"); params.append(name)
                if target_kzt is not None:
                    updates.append("target_amount = ?"); params.append(float(target_kzt))
                if due_date is not None:
                    updates.append("target_date = ?"); params.append(due_date)
                if status is not None:
                    updates.append("status = ?"); params.append(status)

                updates.append("description = ?"); params.append(json.dumps(desc_obj))
                updates.append("updated_at = ?"); params.append(_now_iso())
                params.append(goal_id)

                conn.execute(f"UPDATE goals SET {', '.join(updates)} WHERE id = ?", params)
                log.info(f"[UpdateGoal] UPDATED user_id={user_id}, goal_id={goal_id}")
                return True

        # create new goal
        new_id = goal_id or f"goal_{int(datetime.utcnow().timestamp()*1000)}"
        desc_obj = {}
        if monthly_contribution_kzt is not None:
            desc_obj["monthly_contribution_kzt"] = float(monthly_contribution_kzt)
        if months is not None:
            desc_obj["months"] = int(months)

        conn.execute("""
            INSERT INTO goals (id, user_id, title, description, goal_type, target_amount,
                               current_amount, target_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id,
            user_id,
            name or "Goal",
            json.dumps(desc_obj) if desc_obj else None,
            "savings",
            float(target_kzt) if target_kzt is not None else 0.0,
            0.0,
            due_date,
            status or "active",
            _now_iso()
        ))
        log.info(f"[UpdateGoal] CREATED user_id={user_id}, goal_id={new_id}")
        return True


def create_credit_req(user_id: str, product_id: Optional[str], amount_kzt: float, term_months: int) -> str:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        rid = f"credit_req_{int(datetime.utcnow().timestamp()*1000)}"
        conn.execute("""
            INSERT INTO credit_requests (id, user_id, product_id, amount_kzt, term_months, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'submitted', ?)
        """, (rid, user_id, product_id, float(amount_kzt), int(term_months), _now_iso()))
        log.info(f"[CreateCreditRequest] user_id={user_id}, request_id={rid}")
        return rid

def create_deposit_req(user_id: str, product_id: Optional[str], initial_deposit_kzt: float, term_months: int) -> str:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        rid = f"deposit_req_{int(datetime.utcnow().timestamp()*1000)}"
        conn.execute("""
            INSERT INTO deposit_requests (id, user_id, product_id, initial_deposit_kzt, term_months, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'submitted', ?)
        """, (rid, user_id, product_id, float(initial_deposit_kzt), int(term_months), _now_iso()))
        log.info(f"[CreateDepositRequest] user_id={user_id}, request_id={rid}")
        return rid

# -------------------- Feasibility in KZT majors --------------------

def check_goal_feasibility(
    user_id: str,
    target_kzt: float,
    months: int,
    current_savings_kzt: float = 0.0,
    payment_buffer: float = 0.9,
) -> Dict[str, Any]:
    with _db.get_connection() as conn:
        _ensure_user_row(conn, user_id)
        income_kzt = _read_income_kzt(conn, user_id) or 0.0
        baseline_kzt = _baseline_monthly_expense_kzt(conn, user_id, months=6)
        capacity_kzt = max(0.0, income_kzt - baseline_kzt)

        need_kzt = max(0.0, float(target_kzt) - float(current_savings_kzt or 0.0))
        req_save_pm_kzt = round(need_kzt / max(1, int(months)), 2)
        alloc_kzt = round(capacity_kzt * float(payment_buffer), 2)

        # conservative credit proxy: max principal ≈ monthly alloc × n (ignoring interest)
        credit_max_principal_kzt = round(alloc_kzt * max(1, int(months)), 2)

        deposit_feasible = req_save_pm_kzt <= alloc_kzt
        suggestion = "deposit" if deposit_feasible else "credit"
        reason = (
            "Required monthly saving fits within safe capacity."
            if deposit_feasible
            else "Required monthly saving exceeds safe capacity; consider a loan or extend the timeline."
        )

        return {
            "user_id": user_id,
            "income_monthly_kzt": income_kzt,
            "baseline_monthly_expense_kzt": baseline_kzt,
            "monthly_capacity_kzt": capacity_kzt,
            "payment_buffer": float(payment_buffer),
            "alloc_for_saving_kzt": alloc_kzt,
            "required_saving_per_month_kzt": req_save_pm_kzt,
            "deposit_feasible": deposit_feasible,
            "credit_max_principal_kzt": credit_max_principal_kzt,
            "suggestion": suggestion,
            "reason": reason,
            "months": int(months),
            "target_kzt": float(target_kzt),
            "current_savings_kzt": float(current_savings_kzt or 0.0),
        }

# -------------------- Dispatcher --------------------

def run_tool(name: str, args_json: str | Dict[str, Any]) -> Dict[str, Any]:
    args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
    log.info(f"🛠 Running tool: {name} with args: {args}")

    if name == "GetUserSnapshot":
        return get_snapshot(args["user_id"])

    if name == "UpsertIncome":
        upsert_income(args["user_id"], float(args["income_monthly_kzt"]))
        return {"ok": True}

    if name == "RAGSearch":
        hits = rag.search(args["query"], int(args.get("k", 5)))
        return {"hits": hits}

    if name == "CreateCreditRequest":
        rid = create_credit_req(
            user_id=args["user_id"],
            product_id=args.get("product_id"),
            amount_kzt=float(args["amount_kzt"]),
            term_months=int(args["term_months"]),
        )
        return {"request_id": rid, "status": "submitted"}

    if name == "CreateDepositRequest":
        rid = create_deposit_req(
            user_id=args["user_id"],
            product_id=args.get("product_id"),
            initial_deposit_kzt=float(args["initial_deposit_kzt"]),
            term_months=int(args["term_months"]),
        )
        return {"request_id": rid, "status": "submitted"}

    if name == "UpsertBudget":
        # expects items [{category, amount_kzt}]
        upsert_budget(args["user_id"], args["month"], list(args.get("items", [])))
        return {"ok": True}

    if name == "UpdateBudgetCategory":
        update_budget_category(
            user_id=args["user_id"],
            month=args["month"],
            category=args["category"],
            amount_kzt=float(args["amount_kzt"]),
        )
        return {"ok": True}

    if name == "UpdateGoal":
        update_goal(
            user_id=args["user_id"],
            goal_id=args.get("goal_id"),
            name=args.get("name"),
            monthly_contribution_kzt=args.get("monthly_contribution_kzt"),
            target_kzt=args.get("target_kzt"),
            due_date=args.get("due_date"),
            status=args.get("status"),
            priority=args.get("priority"),
        )
        return {"ok": True}

    if name == "CheckGoalFeasibility":
        return check_goal_feasibility(
            user_id=args["user_id"],
            target_kzt=float(args["target_kzt"]),
            months=int(args["months"]),
            current_savings_kzt=float(args.get("current_savings_kzt", 0.0)),
            payment_buffer=float(args.get("payment_buffer", 0.9)),
        )

    log.warning(f"Unknown tool: {name}")
    return {"error": "unknown tool"}
