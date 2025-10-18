# app/services/tools_impl.py
# -------------------------------------------------
# Implements all tools declared in the SYSTEM_PROMPT "TOOLS" schema.
# Each tool is an async function that receives an AsyncSession (db)
# and returns a plain-JSON-serializable dict matching the tool's contract.
#
# This module also expects the model updates included below to exist.
# -------------------------------------------------
from __future__ import annotations

import math
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    User,
    Transaction,
    Goal,
    Budget,
    BudgetItem,
    CreditRequest,
    DepositRequest,
)

# Optional: a very small facade around your RAG index (if present)
try:
    # Prefer an existing shared RAG singleton, e.g. app.rag.rag
    from app.rag import rag  # type: ignore
except Exception:  # pragma: no cover
    rag = None


# -----------------------------
# Utilities
# -----------------------------

def _to_decimal(x: Any) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")


def _month_floor(d: date | datetime) -> date:
    d = d.date() if isinstance(d, datetime) else d
    return date(d.year, d.month, 1)


async def _get_income_monthly(db: AsyncSession, user_id: str) -> Optional[Decimal]:
    res = await db.execute(select(User.income_monthly_kzt).where(User.id == str(user_id)))
    income = res.scalar_one_or_none()
    return _to_decimal(income) if income is not None else None


async def _avg_monthly_from_income_tx(db: AsyncSession, user_id: str, months: int = 6) -> Optional[Decimal]:
    cutoff = datetime.utcnow().date() - timedelta(days=30 * months)
    q = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == str(user_id),
            Transaction.transaction_type == "income",
            Transaction.transaction_date >= cutoff,
        )
    )
    total = _to_decimal(q.scalar_one() or 0)
    if total <= 0:
        return None
    # Approximate by months param (not unique months)
    return (total / Decimal(months)).quantize(Decimal("0.01"))


async def _avg_monthly_expense(db: AsyncSession, user_id: str, months: int = 6) -> Decimal:
    cutoff = datetime.utcnow().date() - timedelta(days=30 * months)
    q = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == str(user_id),
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= cutoff,
        )
    )
    total = _to_decimal(q.scalar_one() or 0)
    return (total / Decimal(months)).quantize(Decimal("0.01"))


async def _latest_budget_items(db: AsyncSession, user_id: str) -> Dict[str, float]:
    # Return items from the most recent month with a budget, as a {category: amount}
    res = await db.execute(
        select(Budget.id)
        .where(Budget.user_id == str(user_id))
        .order_by(Budget.month.desc())
        .limit(1)
    )
    budget_id = res.scalar_one_or_none()
    if not budget_id:
        return {}
    rows = await db.execute(select(BudgetItem.category, BudgetItem.amount_kzt).where(BudgetItem.budget_id == budget_id))
    items = {}
    for cat, amt in rows.all():
        items[cat] = float(_to_decimal(amt))
    return items


# -----------------------------
# Tools
# -----------------------------

async def GetUserSnapshot(db: AsyncSession, *, user_id: str) -> Dict[str, Any]:
    # income
    income = await _get_income_monthly(db, user_id)

    # last 6 months expenses list (flattened)
    cutoff = datetime.utcnow().date() - timedelta(days=180)
    rows = await db.execute(
        select(
            Transaction.transaction_type,
            Transaction.category,
            Transaction.amount,
            Transaction.description,
            Transaction.transaction_date,
        )
        .where(Transaction.user_id == str(user_id), Transaction.transaction_date >= cutoff)
        .order_by(Transaction.transaction_date.desc())
    )
    expenses = []
    for ttype, cat, amt, desc, tdate in rows.all():
        if ttype == "expense":
            expenses.append(
                {
                    "type": "EXPENSE",
                    "category": cat or "other",
                    "amount_kzt": float(_to_decimal(amt)),
                    "description": desc,
                    "date": str(tdate),
                }
            )

    # goals
    grows = await db.execute(select(Goal.id, Goal.title, Goal.target_amount, Goal.current_amount).where(Goal.user_id == str(user_id)).order_by(Goal.created_at.desc()))
    goals = []
    for gid, title, target, current in grows.all():
        goals.append(
            {
                "id": str(gid),
                "name": title,
                "target_kzt": float(_to_decimal(target)),
                "current_kzt": float(_to_decimal(current)),
                "status": "active",
            }
        )

    budgets = await _latest_budget_items(db, user_id)

    return {
        "user_id": user_id,
        "income_monthly_kzt": float(income) if income is not None else None,
        "transactions": expenses,
        "goals": goals,
        "budgets": budgets,
    }


async def UpsertIncome(db: AsyncSession, *, user_id: str, income_monthly_kzt: float) -> Dict[str, Any]:
    res = await db.execute(select(User).where(User.id == str(user_id)))
    user = res.scalar_one_or_none()
    if not user:
        return {"ok": False, "error": "user_not_found"}
    user.income_monthly_kzt = _to_decimal(income_monthly_kzt)
    await db.commit()
    return {"ok": True}


async def RAGSearch(db: AsyncSession, *, query: str, k: int = 5) -> Dict[str, Any]:  # db kept for signature parity
    if rag is None:
        return {"hits": []}
    hits = rag.search(query, k)  # expected: list of dicts with id/title/url/content/score
    return {"hits": hits}


async def CreateCreditRequest(db: AsyncSession, *, user_id: str, product_id: Optional[str], amount_kzt: float, term_months: int) -> Dict[str, Any]:
    req = CreditRequest(
        user_id=str(user_id),
        product_id=product_id,
        amount_kzt=_to_decimal(amount_kzt),
        term_months=term_months,
        status="pending",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return {"ok": True, "request_id": str(req.id), "status": req.status}


async def CreateDepositRequest(db: AsyncSession, *, user_id: str, product_id: Optional[str], initial_deposit_kzt: float, term_months: int) -> Dict[str, Any]:
    req = DepositRequest(
        user_id=str(user_id),
        product_id=product_id,
        initial_deposit_kzt=_to_decimal(initial_deposit_kzt),
        term_months=term_months,
        status="pending",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return {"ok": True, "request_id": str(req.id), "status": req.status}


async def UpsertBudget(db: AsyncSession, *, user_id: str, month: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    # month format: YYYY-MM-01
    m = datetime.strptime(month, "%Y-%m-%d").date()
    # Find existing budget
    res = await db.execute(select(Budget).where(Budget.user_id == str(user_id), Budget.month == m))
    budget = res.scalar_one_or_none()
    if not budget:
        budget = Budget(user_id=str(user_id), month=m)
        db.add(budget)
        await db.flush()
    else:
        # delete old items
        await db.execute(BudgetItem.__table__.delete().where(BudgetItem.budget_id == budget.id))

    # insert new items
    rows = []
    for it in items:
        cat = (it.get("category") or "other").strip()
        amt = _to_decimal(it.get("amount_kzt", 0))
        rows.append(BudgetItem(budget_id=budget.id, category=cat, amount_kzt=amt))
    db.add_all(rows)
    await db.commit()
    return {"ok": True, "budget_id": str(budget.id), "items": {r.category: float(r.amount_kzt) for r in rows}}


async def UpdateBudgetCategory(db: AsyncSession, *, user_id: str, month: str, category: str, amount_kzt: float) -> Dict[str, Any]:
    m = datetime.strptime(month, "%Y-%m-%d").date()
    res = await db.execute(select(Budget).where(Budget.user_id == str(user_id), Budget.month == m))
    budget = res.scalar_one_or_none()
    if not budget:
        budget = Budget(user_id=str(user_id), month=m)
        db.add(budget)
        await db.flush()

    # Upsert single item
    rowres = await db.execute(
        select(BudgetItem).where(BudgetItem.budget_id == budget.id, BudgetItem.category == category)
    )
    item = rowres.scalar_one_or_none()
    if not item:
        item = BudgetItem(budget_id=budget.id, category=category, amount_kzt=_to_decimal(amount_kzt))
        db.add(item)
    else:
        item.amount_kzt = _to_decimal(amount_kzt)
    await db.commit()
    return {"ok": True, "budget_id": str(budget.id), "category": category, "amount_kzt": float(item.amount_kzt)}


async def UpdateGoal(
    db: AsyncSession,
    *,
    user_id: str,
    goal_id: Optional[str] = None,
    name: Optional[str] = None,
    target_kzt: Optional[float] = None,
    due_date: Optional[str] = None,
    months: Optional[int] = None,
    monthly_contribution_kzt: Optional[float] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
) -> Dict[str, Any]:
    # Load or create
    goal = None
    if goal_id:
        res = await db.execute(select(Goal).where(Goal.id == str(goal_id), Goal.user_id == str(user_id)))
        goal = res.scalar_one_or_none()
    if not goal:
        # create if name+target provided
        if not name or target_kzt is None:
            return {"ok": False, "error": "missing_name_or_target_for_new_goal"}
        goal = Goal(user_id=str(user_id), title=name, target_amount=float(target_kzt), current_amount=0.0)
        db.add(goal)
        await db.flush()
    # apply updates
    if name:
        goal.title = name
    if target_kzt is not None:
        goal.target_amount = float(target_kzt)
    if monthly_contribution_kzt is not None:
        # we don't persist this on the model; return it back for UI
        pass
    if status:
        # not stored, but you may extend the model to persist in future
        pass
    # priority ignored for now

    await db.commit()
    await db.refresh(goal)
    return {
        "ok": True,
        "goal": {
            "id": str(goal.id),
            "name": goal.title,
            "target_kzt": float(goal.target_amount),
            "current_kzt": float(goal.current_amount or 0.0),
        },
    }


async def CheckGoalFeasibility(
    db: AsyncSession,
    *,
    user_id: str,
    target_kzt: float,
    months: int,
    current_savings_kzt: float = 0.0,
    payment_buffer: float = 0.9,
) -> Dict[str, Any]:
    # Income: prefer user profile, else derive from income txns
    income = await _get_income_monthly(db, user_id)
    if income is None:
        income = await _avg_monthly_from_income_tx(db, user_id, months=6) or Decimal("0")

    baseline_exp = await _avg_monthly_expense(db, user_id, months=6)

    capacity = max(Decimal("0"), income - baseline_exp)
    need = max(Decimal("0"), _to_decimal(target_kzt) - _to_decimal(current_savings_kzt))
    req_pm = (need / Decimal(max(1, months))).quantize(Decimal("0.01"))
    alloc = (capacity * _to_decimal(payment_buffer)).quantize(Decimal("0.01"))

    deposit_feasible = bool(income > 0 and req_pm <= alloc)

    return {
        "deposit_feasible": deposit_feasible,
        "required_saving_per_month_kzt": float(req_pm),
        "suggestion": "deposit" if deposit_feasible else "extend_timeline_or_reduce_target",
        "reason": (
            "Required monthly saving fits within capacity."
            if deposit_feasible
            else "Based on your spending patterns, you may need to extend the timeline or reduce the target amount."
        ),
        "months": months,
        "target_kzt": float(target_kzt),
    }


async def GetSpendingAnalysis(db: AsyncSession, *, user_id: str, months: int = 6) -> Dict[str, Any]:
    cutoff = datetime.utcnow().date() - timedelta(days=30 * months)

    # Aggregate by category
    rows = await db.execute(
        select(Transaction.category, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == str(user_id),
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= cutoff,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    totals = rows.all()
    total_spend = sum([_to_decimal(v or 0) for _, v in totals]) or Decimal("0")

    categories = [
        {
            "category": (c or "other"),
            "total_kzt": float(_to_decimal(v or 0)),
            "share": float(((_to_decimal(v or 0) / total_spend) * 100).quantize(Decimal("0.01"))) if total_spend > 0 else 0.0,
        }
        for c, v in totals
    ]

    # Recurring small expenses / subscriptions heuristic
    # Define recurring as same description appearing >= 3 times with avg amount <= 10000 KZT
    rec_rows = await db.execute(
        select(Transaction.description, func.count(Transaction.id), func.avg(Transaction.amount))
        .where(
            Transaction.user_id == str(user_id),
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= cutoff,
        )
        .group_by(Transaction.description)
        .having(func.count(Transaction.id) >= 3)
        .order_by(func.count(Transaction.id).desc())
    )

    recurring = []
    for desc, cnt, avg_amt in rec_rows.all():
        avg_amt_dec = _to_decimal(avg_amt or 0)
        if avg_amt_dec <= Decimal("10000"):
            recurring.append({"description": desc, "count": int(cnt), "avg_amount_kzt": float(avg_amt_dec)})

    return {
        "months": months,
        "total_spend_kzt": float(total_spend),
        "by_category": categories,
        "recurring_small_expenses": recurring,
    }

