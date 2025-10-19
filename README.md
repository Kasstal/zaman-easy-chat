# 🏦 Zaman AI Banking Assistant

**Production-ready AI Banking Assistant** with advanced chatbot, statement parsing, RAG-powered recommendations, and financial goal tracking.

Built with **FastAPI**, **SQLAlchemy**, **OpenAI GPT-4**, and **SQLite**.

---

## ✨ Key Features

### 🤖 **AI-Powered Chatbot**
- **OpenAI GPT-4o-mini** integration with function calling
- **5 Financial Tools**: GetUserSnapshot, UpdateGoal, CheckGoalFeasibility, RAGSearch, UpsertIncome
- **Context-aware conversations** with full transaction & goal history
- **Multi-turn dialogue** with tool execution loop (max 5 iterations)
- **Fallback mode** when API key not set

### 📊 **Smart Statement Parser**
- **Multi-format support**: CSV, Excel (.xlsx, .xls), PDF
- **Kaspi Bank PDF** specialized parser with regex extraction
- **Auto-categorization** of income/expense transactions
- **Generic parsers** for other bank formats
- **No file storage** - only extracted transactions saved
- **Bulk transaction creation** with UUID support

### 🔍 **Enhanced RAG System**
- **Auto-loads documents** from `rag/` folder (7 documents)
- **TF-IDF weighting** for better relevance
- **Cosine similarity** search with configurable k
- **Self-aware metadata**: tracks document count, query history
- **800-character snippets** for context efficiency
- **Cyrillic support** for Kazakh/Russian content

### 🎯 **Advanced Goal Tracking**
- **Create financial goals** with monthly contribution tracking
- **Auto-calculated fields**:
  - `progress_percentage`: Current completion %
  - `remaining_amount`: KZT left to goal
  - `months_to_complete`: Estimated timeline
  - `is_completed`: Achievement status
- **Full CRUD operations**: Create, Read, Update, Delete goals
- **Flexible updates**: Modify amount, contribution, title, target

### 💾 **Robust Database Architecture**
- **UUID-based primary keys** (String(36) for SQLite compatibility)
- **5 Core models**: User, Chat, Message, Transaction, Goal
- **Extended models**: Budget, BudgetItem, CreditRequest, DepositRequest
- **Cascade deletes** for data integrity
- **Async SQLAlchemy** for high performance
- **Auto-initialization** on startup

---

## 🏗️ Project Structure

```
zaman-easy-chat/
├── app/
│   ├── models/
│   │   └── models.py              # SQLAlchemy ORM models (UUID-based)
│   ├── schemas/
│   │   └── schemas.py             # Pydantic validation schemas
│   ├── crud/
│   │   └── crud.py                # Database CRUD operations
│   ├── services/
│   │   ├── parser_service.py      # ✅ Bank statement parser (CSV/Excel/PDF)
│   │   └── chatbot_service/
│   │       ├── chatbot_service.py # ✅ OpenAI chatbot with tools
│   │       ├── rag_service.py     # ✅ Enhanced RAG with TF-IDF
│   │       ├── tools_impl.py      # Financial tool implementations
│   │       ├── tools_schema.py    # Tool JSON schemas for OpenAI
│   │       └── system_prompt.py   # System prompt configuration
│   ├── routers/
│   │   ├── users.py               # User & goal endpoints
│   │   ├── chatbot.py             # Chat endpoints
│   │   └── parser.py              # Statement upload endpoints
│   ├── config.py                  # Application settings
│   └── database.py                # Async database setup
├── rag/                            # ✅ RAG documents (auto-loaded)
│   ├── credit.txt
│   ├── deposit.txt
│   ├── finance.txt
│   ├── kopilka.txt
│   ├── mortgage.txt
│   ├── vakala.txt
│   └── рассрочка.txt
├── main.py                         # FastAPI application
├── start.py                        # Quick start script
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
└── zaman.db                        # SQLite database (auto-created)
```

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Set Environment Variables
Create `.env` file:
```bash
# Required for AI chatbot
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database (default values)
DATABASE_URL=sqlite+aiosqlite:///./zaman.db
ENVIRONMENT=development
DEBUG=True
```

### 3️⃣ Start the Server
```bash
python start.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4️⃣ Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

---

## 📡 API Endpoints

### 👤 **Users & Goals**
```http
POST   /users/                      # Create new user (auto-creates chat)
GET    /users/{user_id}             # Get user details
POST   /users/{user_id}/goals       # Create financial goal
GET    /users/{user_id}/goals       # List all goals (with calculations)
GET    /users/goals/{goal_id}       # Get specific goal
PUT    /users/goals/{goal_id}       # Update goal (amount/contribution/title/target)
DELETE /users/goals/{goal_id}       # Delete goal
```

### 💬 **Chatbot**
```http
POST   /chatbot/chat                # Send message, get AI response
GET    /chatbot/messages/{user_id}  # Get chat history
```

### 📄 **Statement Parser**
```http
POST   /parser/upload-statement/{user_id}  # Upload CSV/Excel/PDF statement
GET    /parser/transactions/{user_id}      # Get all transactions
```

---

## 💡 Usage Examples

### Create a User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe"}'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "created_at": "2025-10-19T10:00:00"
}
```

### Create a Goal
```bash
curl -X POST "http://localhost:8000/users/550e8400-e29b-41d4-a716-446655440000/goals" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Vacation Fund",
    "target_amount": 500000,
    "monthly_contribution": 50000
  }'
```

**Response with Auto-Calculations:**
```json
{
  "id": "goal-uuid",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Vacation Fund",
  "target_amount": 500000.0,
  "current_amount": 0.0,
  "monthly_contribution": 50000.0,
  "created_at": "2025-10-19T10:05:00",
  "progress_percentage": 0.0,
  "remaining_amount": 500000.0,
  "months_to_complete": 10.0,
  "is_completed": false
}
```

### Upload Bank Statement
```bash
curl -X POST "http://localhost:8000/parser/upload-statement/550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@statement.pdf"
```

### Chat with AI
```bash
curl -X POST "http://localhost:8000/chatbot/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Я хочу накопить 500,000 тенге на отпуск за 6 месяцев. Реально ли это?"
  }'
```

**AI Response:**
```json
{
  "response": "На основе ваших транзакций, средний ежемесячный расход составляет...",
  "message_id": "message-uuid"
}
```

---

## Database Models

- **User**: User account (one user, one chat)
- **Chat**: Chat session for user
- **Message**: Chat messages (user/assistant)
- **Transaction**: Parsed bank transactions
- **Goal**: Financial goals with progress tracking

## Integration Points

The following sections are ready for your existing logic integration:

1. **Chatbot Logic** (`app/routers/chatbot.py`):
   - Integrate your LLM + Whisper logic in the `/chat` endpoint
   - User messages are saved automatically
   - Return AI response to be saved

2. **Parser Logic** (`app/routers/parser.py`):
   - Integrate your statement parsing logic in `/upload-statement/{user_id}`
   - Files are not stored, only parsed transactions
   - Return list of `TransactionCreate` objects

## Development

- Database: SQLite (`zaman.db`)
- All tables created automatically on startup
- Async SQLAlchemy for better performance
- Pydantic for request/response validation

## Next Steps

1. Integrate your chatbot logic
2. Integrate your parser logic
3. Add authentication if needed
4. Deploy to production
