"""
orchestrator.py
---------------
Main loop orchestrating LLM ↔ tool interactions.

Handles:
- Calling GPT model with your SYSTEM_PROMPT
- Executing tool calls (function calling)
- Feeding tool results back into conversation
- Returning the final assistant message

This version is fixed to avoid the 400 error
("Invalid type for messages[x].content") by
JSON-encoding tool results before re-sending.
"""

import json
from typing import Dict, Any, List
from openai import OpenAI

# ✅ Relative imports inside package
from .tools_schema import TOOLS
from ..services.tools_impl import run_tool

SYSTEM_PROMPT = """
You are a diligent personal finance assistant. Respond in the user's language.

Core rules:
- Always call GetUserSnapshot first to get income, spending, and goals.
- If income is missing, ask for it and call UpsertIncome (KZT major units).

Goals:
- When the user states a goal, parse: {name, target_kzt, due_date OR months, monthly_contribution_kzt if said}.
- Call UpdateGoal with these fields. If monthly_contribution_kzt is not provided but {target_kzt, months} are, still call UpdateGoal; the tool will set a monthly contribution automatically.
- Then call CheckGoalFeasibility (target_kzt, months, current_savings_kzt if known) and advise:
  - Unreasonable vs. capacity → suggest loan or a longer timeline (explain briefly).
  - Reasonable → suggest opening a deposit; outline plan.
- Before CreateDepositRequest or CreateCreditRequest, restate terms and ask for explicit confirmation.

Budgets:
- After key profile changes or first session, propose a monthly budget (UpsertBudget), including goal monthly contributions.

Clarity:
- Be explicit with KZT amounts and months. Keep messages short and actionable.
"""



def chat_turn(client: OpenAI, user_id: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    One full turn including potential tool calls until the model returns a final assistant message.
    Automatically executes any tools requested by the model.
    """
    # prepare tool specs
    functions = [
        {
            "name": t["name"],
            "parameters": t["parameters"],
            "description": t["description"],
        }
        for t in TOOLS
    ]

    while True:
        # --- Step 1: send to model ---
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"USER_ID={user_id}"},
                *messages,
            ],
            tools=[{"type": "function", "function": f} for f in functions],
            tool_choice="auto",
            temperature=0.2,
        )

        msg = resp.choices[0].message

        # --- Step 2: If model requested tools ---
        if msg.tool_calls:
            tool_msg_bundle = []

            for call in msg.tool_calls:
                name = call.function.name

                # Parse arguments safely
                try:
                    args = (
                        json.loads(call.function.arguments)
                        if isinstance(call.function.arguments, str)
                        else (call.function.arguments or {})
                    )
                except Exception:
                    args = {}

                # Execute tool
                result = run_tool(name, args)

                # ✅ Encode tool result as JSON string (fixes 400 Bad Request)
                tool_msg_bundle.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            # Add the assistant message that triggered tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            # Add all tool outputs
            messages.extend(tool_msg_bundle)

            # loop again — the model now "sees" the tool results
            continue

        # --- Step 3: No tool call -> return final message ---
        return {"assistant_message": msg.content or ""}
