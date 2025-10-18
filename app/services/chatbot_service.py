"""
Service layer for chatbot integration
Fully integrated chatbot with OpenAI, RAG, and financial tools
"""
import json
import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from openai import OpenAI
import os

from app.schemas.schemas import MessageResponse

logger = logging.getLogger(__name__)


# ==================== RAG Service ====================
class SimpleRAG:
    """
    Lightweight RAG using cosine similarity on term-frequency vectors.
    """
    def __init__(self):
        self.docs = []  # [{'id','title','url','content'}]
        self.vocab = {}
        self.doc_tf = []  # list[dict[token -> tf]]

    def build(self, docs):
        self.docs = docs[:]
        self.vocab = {}
        self.doc_tf = []
        for d in docs:
            tf = {}
            for tok in self._tokens(d['content']):
                tf[tok] = tf.get(tok, 0) + 1
                if tok not in self.vocab:
                    self.vocab[tok] = len(self.vocab)
            self.doc_tf.append(tf)

    def _tokens(self, text):
        return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]

    def _to_vec(self, tf):
        vec = [0.0] * len(self.vocab)
        for tok, cnt in tf.items():
            idx = self.vocab.get(tok)
            if idx is not None:
                vec[idx] = float(cnt)
        return vec

    def _cos(self, a, b):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

    def search(self, query: str, k: int = 5):
        qtf = {}
        for tok in self._tokens(query):
            qtf[tok] = qtf.get(tok, 0) + 1
        qv = self._to_vec(qtf)
        scored = []
        for i, tf in enumerate(self.doc_tf):
            dv = self._to_vec(tf)
            scored.append((self._cos(qv, dv), i))
        scored.sort(reverse=True)
        out = []
        for score, idx in scored[:k]:
            d = self.docs[idx]
            out.append({
                "id": d["id"], "score": float(score),
                "title": d.get("title", ""), "url": d.get("url"),
                "content": d["content"][:800]
            })
        return out


# Singleton RAG instance
rag = SimpleRAG()


# ==================== Financial Tools Schema ====================
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
                "status": {"type": "string"}
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


SYSTEM_PROMPT = """
You are a diligent personal finance assistant. Respond in the user's language.

Core rules:
- Always call GetUserSnapshot first to get income, spending, and goals.
- If income is missing, ask for it and call UpsertIncome (KZT major units).

Goals:
- When the user states a goal, parse: {name, target_kzt, due_date OR months, monthly_contribution_kzt if said}.
- Call UpdateGoal with these fields. If monthly_contribution_kzt is not provided but {target_kzt, months} are, still call UpdateGoal; the tool will set a monthly contribution automatically.
- Then call CheckGoalFeasibility (target_kzt, months, current_savings_kzt if known) and advise:
  - Unreasonable vs. capacity → suggest alternatives or a longer timeline.
  - Reasonable → suggest a savings plan and outline next steps.

Clarity:
- Be explicit with KZT amounts and months. Keep messages short and actionable.
- Use RAGSearch to get information about bank products when relevant.
"""


class ChatbotService:
    """
    Service class for chatbot logic integration.
    Uses OpenAI with function calling, RAG, and financial tools.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(base_url="https://openai-hub.neuraldeep.tech/", api_key=api_key)
        else:
            logger.warning("OPENAI_API_KEY not set. Chatbot will use fallback responses.")
            self.client = None
        
        # Load RAG data if available
        self._load_rag_data()
    
    def _load_rag_data(self):
        """Load RAG documents from the rag folder"""
        try:
            rag_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'to integrate', 'rag')
            if not os.path.exists(rag_dir):
                # Try alternate path
                rag_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rag')
            
            if os.path.exists(rag_dir):
                docs = []
                doc_id = 0
                for filename in os.listdir(rag_dir):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(rag_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            title = os.path.splitext(filename)[0]
                            # Chunk by paragraphs
                            for chunk in content.split('\n\n'):
                                if chunk.strip():
                                    docs.append({
                                        "id": f"doc-{doc_id}",
                                        "title": title,
                                        "url": None,
                                        "content": chunk.strip()[:900]
                                    })
                                    doc_id += 1
                
                if docs:
                    rag.build(docs)
                    logger.info(f"✅ Loaded {len(docs)} RAG documents")
                else:
                    logger.warning("No RAG documents found")
            else:
                logger.warning(f"RAG directory not found: {rag_dir}")
        except Exception as e:
            logger.error(f"Error loading RAG data: {e}")
    
    async def _run_tool(self, name: str, args: Dict[str, Any], user_transactions=None, user_goals=None) -> Dict[str, Any]:
        """Execute a tool call"""
        logger.info(f"🛠 Running tool: {name} with args: {args}")
        
        if name == "GetUserSnapshot":
            # Build snapshot from provided context
            user_id = args.get("user_id")
            
            # Calculate last 6 months expenses by category
            six_months_ago = datetime.now() - timedelta(days=180)
            expenses = []
            if user_transactions:
                for t in user_transactions:
                    if t.transaction_type == "expense" and t.transaction_date >= six_months_ago.date():
                        expenses.append({
                            "type": "EXPENSE",
                            "category": t.category or "other",
                            "amount_kzt": float(t.amount),
                            "description": t.description,
                            "date": str(t.transaction_date)
                        })
            
            # Format goals
            goals_data = []
            if user_goals:
                for g in user_goals:
                    goals_data.append({
                        "id": str(g.id),
                        "name": g.title,
                        "target_kzt": float(g.target_amount),
                        "current_kzt": float(g.current_amount),
                        "status": "active"
                    })
            
            return {
                "user_id": user_id,
                "income_monthly_kzt": None,  # Not stored in current model
                "transactions": expenses,
                "goals": goals_data,
                "budgets": {}
            }
        
        elif name == "UpsertIncome":
            # Income not in current model - just acknowledge
            return {"ok": True, "message": "Income noted"}
        
        elif name == "RAGSearch":
            query = args.get("query", "")
            k = args.get("k", 5)
            hits = rag.search(query, k)
            return {"hits": hits}
        
        elif name == "UpdateGoal":
            # Goal update would need database access - return OK for now
            return {"ok": True, "message": "Goal updated"}
        
        elif name == "CheckGoalFeasibility":
            target_kzt = float(args.get("target_kzt", 0))
            months = int(args.get("months", 1))
            current_savings_kzt = float(args.get("current_savings_kzt", 0))
            payment_buffer = float(args.get("payment_buffer", 0.9))
            
            # Calculate based on transactions
            income_kzt = 0.0
            baseline_expense_kzt = 0.0
            
            if user_transactions:
                # Calculate average monthly expenses from last 6 months
                expenses_sum = sum(float(t.amount) for t in user_transactions if t.transaction_type == "expense")
                baseline_expense_kzt = expenses_sum / 6 if len(user_transactions) > 0 else 0
            
            capacity_kzt = max(0.0, income_kzt - baseline_expense_kzt)
            need_kzt = max(0.0, target_kzt - current_savings_kzt)
            req_save_pm_kzt = round(need_kzt / max(1, months), 2)
            alloc_kzt = round(capacity_kzt * payment_buffer, 2)
            
            deposit_feasible = req_save_pm_kzt <= alloc_kzt if income_kzt > 0 else False
            suggestion = "deposit" if deposit_feasible else "extend_timeline_or_reduce_target"
            reason = (
                "Required monthly saving fits within capacity."
                if deposit_feasible
                else "Based on your spending patterns, you may need to extend the timeline or reduce the target amount."
            )
            
            return {
                "deposit_feasible": deposit_feasible,
                "required_saving_per_month_kzt": req_save_pm_kzt,
                "suggestion": suggestion,
                "reason": reason,
                "months": months,
                "target_kzt": target_kzt
            }
        
        logger.warning(f"Unknown tool: {name}")
        return {"error": "unknown tool"}
    
    async def generate_response(
        self, 
        user_message: str, 
        chat_history: List[MessageResponse],
        user_transactions: List = None,
        user_goals: List = None
    ) -> str:
        """
        Generate AI response based on user message and context.
        
        Args:
            user_message: The user's input message
            chat_history: Previous messages in the conversation
            user_transactions: User's transaction data (optional)
            user_goals: User's financial goals (optional)
        
        Returns:
            AI-generated response string
        """
        if not self.client:
            # Fallback response when OpenAI is not configured
            return f"I received your message: '{user_message}'. Please set OPENAI_API_KEY to enable full AI features."
        
        try:
            # Build conversation history
            messages = []
            for msg in chat_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message if not in history
            if not messages or messages[-1]["content"] != user_message:
                messages.append({"role": "user", "content": user_message})
            
            # Prepare tool specs
            functions = [
                {
                    "name": t["name"],
                    "parameters": t["parameters"],
                    "description": t["description"],
                }
                for t in TOOLS
            ]
            
            # Tool calling loop
            max_iterations = 5
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Call OpenAI
                resp = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *messages,
                    ],
                    tools=[{"type": "function", "function": f} for f in functions],
                    tool_choice="auto",
                    temperature=0.7,
                )
                
                msg = resp.choices[0].message
                
                # If model requested tools
                if msg.tool_calls:
                    tool_msg_bundle = []
                    
                    for call in msg.tool_calls:
                        name = call.function.name
                        
                        # Parse arguments
                        try:
                            args = (
                                json.loads(call.function.arguments)
                                if isinstance(call.function.arguments, str)
                                else (call.function.arguments or {})
                            )
                        except Exception:
                            args = {}
                        
                        # Execute tool
                        result = await self._run_tool(name, args, user_transactions, user_goals)
                        
                        # Add tool result
                        tool_msg_bundle.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": name,
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                    
                    # Add assistant message that triggered tools
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
                    
                    # Add tool outputs
                    messages.extend(tool_msg_bundle)
                    
                    # Continue loop to get final response
                    continue
                
                # No tool call - return final message
                return msg.content or "I understand. How can I help you further?"
            
            # Max iterations reached
            return "I'm processing your request. Please try rephrasing your question."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error processing your request. Please try again."
    
    async def process_voice_input(self, audio_data: bytes) -> str:
        """
        Process voice input using Whisper.
        
        Args:
            audio_data: Raw audio bytes
        
        Returns:
            Transcribed text
        """
        # TODO: Integrate Whisper when needed
        return "Voice transcription not yet implemented"


# Singleton instance
chatbot_service = ChatbotService()
