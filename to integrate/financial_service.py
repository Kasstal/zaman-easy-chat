# chatbot/financial_service.py
from collections import defaultdict
from math import floor

SAFETY = 1.05

def average_spend_by_category(txns, months=6):
    """
    txns: list of dict {amount_cents:int, category:str, type:'INCOME'|'EXPENSE'}
    Returns dict[category] -> avg monthly amount_cents (positive values).
    """
    by_cat = defaultdict(list)
    for t in txns:
        if t.get("type") == "EXPENSE" and t.get("amount_cents", 0) > 0:
            by_cat[t["category"]].append(t["amount_cents"])
    return {c: int(sum(v)/max(1,len(v)) * SAFETY) for c, v in by_cat.items()}

def allocate_goals(user_income_cents, avg_by_cat, goals, fixed_categories=None, variable_categories=None):
    fixed_categories = fixed_categories or ["Rent", "Utilities", "Internet", "Phone"]
    variable_categories = variable_categories or [c for c in avg_by_cat if c not in fixed_categories]

    fixed_total = sum(avg_by_cat.get(c, 0) for c in fixed_categories)
    variable_total = sum(avg_by_cat.get(c, 0) for c in variable_categories)
    base_spend = fixed_total + variable_total
    savings_capacity = max(0, user_income_cents - base_spend)

    locked = sum(g.get("monthly_contribution_cents", 0) or 0 for g in goals if g.get("status", "active") == "active")
    remaining = max(0, savings_capacity - locked)

    # weight by inverse priority (1=high -> weight=5; 5=low -> weight=1)
    weights = []
    for g in goals:
        if g.get("status", "active") != "active":
            continue
        fixed = g.get("monthly_contribution_cents")
        if fixed:
            weights.append((g["id"], fixed, True))
        else:
            w = (6 - min(5, int(g.get("priority", 3))))
            weights.append((g["id"], w, False))

    weight_sum = sum(w for _, w, fixed in weights if not fixed) or 1
    plan = {}
    for gid, w, fixed in weights:
        if fixed:
            plan[gid] = w
        else:
            plan[gid] = floor(remaining * (w / weight_sum))

    # if over budget, scale variable categories
    over = sum(plan.values()) + base_spend - user_income_cents
    if over > 0 and variable_total > 0:
        scale = max(0, (variable_total - over)) / variable_total
        for c in variable_categories:
            avg_by_cat[c] = floor(avg_by_cat.get(c, 0) * scale)

    items = [{"category": c, "amount_cents": amt} for c, amt in avg_by_cat.items()]
    return items, plan
