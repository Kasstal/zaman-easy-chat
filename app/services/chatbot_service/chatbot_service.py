# app/services/chatbot_service/chatbot_service.py
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from . import tools_impl as TI
from .system_prompt import SYSTEM_PROMPT
from .tools_schema import TOOLS
from ..parser_service import logger

# Import your tool implementations

# Import your prompt + tool schema (keep in a dedicated module)
# If these live in this file in your project, remove these imports and inline them.

# Optional RAG singleton (safe-import)
try:
    from app.rag import rag  # type: ignore
except Exception:
    rag = None  # noqa: N816



# -----------------------------
# Config (env-driven)
# -----------------------------
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # e.g. https://openai-hub.neuraldeep.tech/v1
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -----------------------------
# Helpers
# -----------------------------
def _load_rag_data(self) -> None:
    """Loads and indexes RAG documents at startup."""

    # ✅ 1. Discover rag directory
    root = _rag_root_dir()
    if not root:
        logger.warning("RAG directory not found (looked for 'to integrate/rag' or 'rag')")
        return

    # ✅ 2. Load text files
    docs = _load_text_files(root)
    if not docs:
        logger.warning("RAG: no .txt documents found under %s", root)
        return

    # ✅ 3. Build the RAG index — put your line HERE
    rag.build(docs)
    logger.info("✅ RAG index loaded with %d chunks from %s", len(docs), root)

def _safe_parse_args(raw_args: Any) -> Dict[str, Any]:
    """Parse tool call arguments robustly to a dict."""
    if raw_args is None:
        return {}
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        s = raw_args.strip()
        if not s or s.lower() == "null":
            return {}
        try:
            return json.loads(s)
        except Exception:
            logger.warning("Tool args JSON parse failed, args=%r", raw_args)
            return {}
    return {}
def _chunk_text_by_paragraphs(text: str, max_chars: int = 900):
    # split on blank lines; further chunk if paragraph > max_chars
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        if len(p) <= max_chars:
            out.append(p)
        else:
            # hard wrap long paragraphs
            for i in range(0, len(p), max_chars):
                out.append(p[i:i+max_chars])
    return out

def _rag_root_dir():
    # prefer "<repo>/to integrate/rag", fallback to "<repo>/rag"
    here = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    p1 = os.path.join(here, "to integrate", "rag")
    if os.path.exists(p1):
        return p1
    p2 = "app/rag"
    return p2 if os.path.exists(p2) else None

def _load_text_files(root: str):
    docs = []
    doc_id = 0
    for fn in os.listdir(root):
        if not fn.lower().endswith(".txt"):
            continue
        path = os.path.join(root, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning("RAG: failed reading %s: %s", path, e)
            continue
        title = os.path.splitext(fn)[0]
        for chunk in _chunk_text_by_paragraphs(content, max_chars=900):
            docs.append({
                "id": f"doc-{doc_id}",
                "title": title,
                "url": None,
                "content": chunk,
            })
            doc_id += 1
    return docs

# -----------------------------
# Service
# -----------------------------
class ChatbotService:
    """
    Service class for chatbot logic integration.
    Uses OpenAI with tool/function calling, RAG, and financial tools.
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self.db: Optional[AsyncSession] = db

        # OpenAI client (works with proxy or official API)
        if OPENAI_API_KEY:
            try:
                if OPENAI_BASE_URL:
                    self.client = OpenAI(base_url=OPENAI_BASE_URL.rstrip("/"), api_key=OPENAI_API_KEY)
                else:
                    self.client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                logger.exception("Failed to init OpenAI client")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not set. Chatbot will use fallback responses.")
            self.client = None

        # Lazy-load/prepare RAG index if your project uses local text files
        self._load_rag_data()

    # -------------------------
    # Internal utilities
    # -------------------------
    def _load_rag_data(self) -> None:
        """Best-effort load of local RAG docs (non-fatal if unavailable)."""
        if rag is None:
            logger.info("RAG index not configured (app.rag.rag missing)")
            return
        try:
            # If your RAG is already built elsewhere, skip.
            # Otherwise, you can populate here if needed.
            logger.info("RAG index available — ready for search")
        except Exception as e:  # pragma: no cover
            logger.warning("Error initializing RAG: %s", e)

    async def _dispatch_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to concrete implementations with full logging."""
        if not isinstance(self.db, AsyncSession):
            logger.error("❌ No AsyncSession attached to ChatbotService, cannot run tool=%s", name)
            return {"error": "no_db_session"}

        func_map = {
            "GetUserSnapshot": TI.GetUserSnapshot,
            "UpsertIncome": TI.UpsertIncome,
            "RAGSearch": TI.RAGSearch,
            "CreateCreditRequest": TI.CreateCreditRequest,
            "CreateDepositRequest": TI.CreateDepositRequest,
            "UpsertBudget": TI.UpsertBudget,
            "UpdateBudgetCategory": TI.UpdateBudgetCategory,
            "UpdateGoal": TI.UpdateGoal,
            "CheckGoalFeasibility": TI.CheckGoalFeasibility,
            "GetSpendingAnalysis": TI.GetSpendingAnalysis,
        }
        func = func_map.get(name)
        if not func:
            logger.warning("Unknown tool requested: %s", name)
            return {"error": "unknown_tool", "name": name}

        try:
            logger.info("🛠 tool_request name=%s args=%s", name, json.dumps(args, ensure_ascii=False))
            result = await func(self.db, **(args or {}))
            # Truncate very large outputs for logs
            payload = json.dumps(result, ensure_ascii=False)
            if len(payload) > 4000:
                payload = payload[:4000] + "..."
            logger.info("🛠 tool_response name=%s result=%s", name, payload)
            return result
        except TypeError as te:
            logger.exception("Tool %s arg error: %s", name, te)
            return {"error": "invalid_args", "detail": str(te)}
        except Exception as e:  # pragma: no cover
            logger.exception("Tool %s failed", name)
            return {"error": "tool_failed", "detail": str(e)}

    # -------------------------
    # Public API
    # -------------------------
    async def generate_response(
            self,
            user_message: str,
            chat_history: List[Any],
            user_transactions: Optional[List[Any]] = None,  # kept for compatibility
            user_goals: Optional[List[Any]] = None,  # kept for compatibility
            *,
            user_id: str,  # REQUIRED so the model can call tools with the correct user_id
    ) -> str:
        """
        Generate AI response based on user message and context.
        - Injects CURRENT_USER_ID to let the model include it in tool calls.
        - Orchestrates tools-only flow per SYSTEM_PROMPT.
        """
        if not self.client:
            return (
               "⚠️ Chatbot service is not currently available."
            )

        # Build conversation history (last 10 messages)
        messages: List[Dict[str, str]] = [
            {"role": msg.role, "content": msg.content} for msg in chat_history[-10:]
        ]
        if not messages or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # Tool specs taken from TOOLS schema
        functions = [
            {"name": t["name"], "parameters": t["parameters"], "description": t["description"]}
            for t in TOOLS
        ]

        # Inject the CURRENT_USER_ID so the model can pass it to tools
        system_ctx = {
            "role": "system",
            "content": (
                f"CURRENT_USER_ID={user_id}\n"
                f"Use CURRENT_USER_ID as `user_id` in all tool calls that require it."
            ),
        }

        max_iterations = 5
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1

                resp = self.client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        system_ctx,
                        *messages,
                    ],
                    tools=[{"type": "function", "function": f} for f in functions],
                    tool_choice="auto",
                    temperature=0.7,
                )

                msg = resp.choices[0].message

                # If the model requested tool calls
                if getattr(msg, "tool_calls", None):
                    tool_msgs: List[Dict[str, Any]] = []

                    for call in msg.tool_calls:
                        name = call.function.name
                        args = _safe_parse_args(call.function.arguments)

                        # Tool dispatch (logs request/response to Uvicorn via logger)
                        result = await self._dispatch_tool(name, args)

                        tool_msgs.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": name,
                            "content": json.dumps(result, ensure_ascii=False),
                        })

                    # Record the assistant message that triggered tools
                    messages.append({
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
                    })

                    # Add tool outputs and continue the loop
                    messages.extend(tool_msgs)
                    continue

                # No tool call -> final natural language answer
                return msg.content or "I understand. How can I help you further?"

            # Safety valve
            return "I'm processing your request. Please try rephrasing your question."

        except Exception as e:
            err = str(e)
            # Make proxy/openai auth errors explicit for easier diagnosis
            if "token_not_found_in_db" in err or "Authentication Error" in err:
                hint = (
                    "Auth error from LLM proxy. Verify OPENAI_BASE_URL and OPENAI_API_KEY. "
                    "If using a proxy, the key must exist in its token DB. "
                    "If calling OpenAI directly, unset OPENAI_BASE_URL and provide a valid sk-* key."
                )
                logger.error("OpenAI/Auth error: %s", err)
                return f"⚠️ LLM authentication failed. {hint}"
            logger.exception("Error generating response")
            return "I encountered an error processing your request. Please try again."

    async def process_voice_input(self, audio_data: bytes) -> str:
        """Placeholder for Whisper or other STT integration."""
        return "Voice transcription not yet implemented"


# Singleton instance
chatbot_service = ChatbotService()
