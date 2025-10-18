TOOLS = [
    {
        "name": "GetUserSnapshot",
        "description": "Return user profile, income (KZT), goals, and last-6-month spend by category.",
        "parameters": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"]
        }
    },
    {
        "name": "UpsertIncome",
        "description": "Set/update monthly income in KZT (major units).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "income_monthly_kzt": {"type": "number"}
            },
            "required": ["user_id", "income_monthly_kzt"]
        }
    },
    {
        "name": "RAGSearch",
        "description": "Retrieve top bank product passages for a user query.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 5}},
            "required": ["query"]
        }
    },
    {
        "name": "CreateCreditRequest",
        "description": "Create a mock credit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "product_id": {"type": "string"},
                "amount_kzt": {"type": "number"},
                "term_months": {"type": "integer"}
            },
            "required": ["user_id", "amount_kzt", "term_months"]
        }
    },
    {
        "name": "CreateDepositRequest",
        "description": "Create a mock deposit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "product_id": {"type": "string"},
                "initial_deposit_kzt": {"type": "number"},
                "term_months": {"type": "integer"}
            },
            "required": ["user_id", "initial_deposit_kzt", "term_months"]
        }
    },
    {
        "name": "UpsertBudget",
        "description": "Create/replace monthly budget (batch) in KZT.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "month": {"type": "string", "description": "YYYY-MM-01"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"category": {"type": "string"}, "amount_kzt": {"type": "number"}},
                        "required": ["category", "amount_kzt"]
                    }
                }
            },
            "required": ["user_id", "month", "items"]
        }
    },
    {
        "name": "UpdateBudgetCategory",
        "description": "Update a single category budget for a month (KZT).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "month": {"type": "string"},
                "category": {"type": "string"},
                "amount_kzt": {"type": "number"}
            },
            "required": ["user_id", "month", "category", "amount_kzt"]
        }
    },
    {
        "name": "UpdateGoal",
        "description": "Create/update a goal (name / target_kzt / due_date or months / monthly_contribution_kzt / status).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "goal_id": {"type": "string"},
                "name": {"type": "string"},
                "target_kzt": {"type": "number"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                "months": {"type": "integer", "description": "Alternatively, give months instead of a due_date."},
                "monthly_contribution_kzt": {"type": "number"},
                "status": {"type": "string"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["user_id"]
        }
    },

    {
        "name": "CheckGoalFeasibility",
        "description": "Evaluate feasibility for a goal (KZT).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "target_kzt": {"type": "number"},
                "months": {"type": "integer"},
                "current_savings_kzt": {"type": "number", "default": 0},
                "payment_buffer": {"type": "number", "default": 0.9}
            },
            "required": ["user_id", "target_kzt", "months"]
        }
    }
]
