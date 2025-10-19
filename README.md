# 🏦 Zaman AI Banking Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg)](https://www.typescriptlang.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://github.com)

**Full-stack AI Banking Assistant** with advanced chatbot, statement parsing, RAG-powered recommendations, and financial goal tracking.

**Backend**: FastAPI + SQLAlchemy + OpenAI GPT-4 + SQLite  
**Frontend**: React 19 + TypeScript + Vite + TailwindCSS

> 🎯 **Hackathon Project** - Complete AI-powered financial management platform

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

### 🎨 **Modern Frontend**
- **React 19** with latest features and performance
- **TypeScript** for type safety
- **Vite** for lightning-fast development
- **TailwindCSS** for beautiful, responsive UI
- **React Router** for navigation (ChatPage, GoalsPage)
- **React Markdown** for AI response rendering
- **Context API** for global user state
- **Responsive Design** - Mobile, tablet, desktop ready

---

## 🏗️ Project Structure

```
zaman-easy-chat/
├── app/                            # 🐍 Backend (FastAPI)
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
│
├── frontend/                       # ⚛️ Frontend (React + TypeScript)
│   ├── src/
│   │   ├── App.tsx                # Main app component
│   │   ├── ChatPage.tsx           # Chat interface page
│   │   ├── GoalsPage.tsx          # Goals management page
│   │   ├── contexts/
│   │   │   └── UserContext.tsx    # Global user state
│   │   ├── assets/                # Static assets
│   │   ├── App.css                # Global styles
│   │   └── main.tsx               # React entry point
│   ├── public/                    # Public assets
│   ├── index.html                 # HTML template
│   ├── package.json               # npm dependencies
│   ├── vite.config.ts             # Vite configuration
│   ├── tailwind.config.js         # TailwindCSS config
│   └── tsconfig.json              # TypeScript config
│
├── rag/                            # ✅ RAG documents (auto-loaded)
│   ├── credit.txt
│   ├── deposit.txt
│   ├── finance.txt
│   ├── kopilka.txt
│   ├── mortgage.txt
│   ├── vakala.txt
│   └── рассрочка.txt
│
├── main.py                         # FastAPI application
├── start.py                        # Quick start script
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
└── zaman.db                        # SQLite database (auto-created)
```

---

## 🚀 Quick Start

### Backend Setup

#### 1️⃣ Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 2️⃣ Set Environment Variables
Create `.env` file:
```bash
# Required for AI chatbot
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database (default values)
DATABASE_URL=sqlite+aiosqlite:///./zaman.db
ENVIRONMENT=development
DEBUG=True
```

#### 3️⃣ Start Backend Server
```bash
python start.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4️⃣ Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

---

### Frontend Setup

#### 1️⃣ Navigate to Frontend Directory
```bash
cd frontend
```

#### 2️⃣ Install Node Dependencies
```bash
npm install
```

#### 3️⃣ Start Development Server
```bash
npm run dev
```

Frontend will be available at: **http://localhost:5173**

#### 4️⃣ Build for Production
```bash
npm run build
npm run preview
```

---

### Full Stack Development

Run both backend and frontend simultaneously:

**Terminal 1** (Backend):
```bash
python start.py
```

**Terminal 2** (Frontend):
```bash
cd frontend && npx vite
```

Then access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs

---

## 🎨 Frontend Features

### Pages

#### 💬 **Chat Page** (`/chat`)
- Real-time AI conversation interface
- Message history with user/assistant distinction
- Markdown rendering for formatted AI responses
- Auto-scroll to latest message
- Input field with send button
- Loading states during API calls

#### 🎯 **Goals Page** (`/goals`)
- List all financial goals with progress bars
- Create new goals form
- Update goal progress inline
- Delete goals functionality
- Visual progress indicators
- Calculated fields display:
  - Progress percentage
  - Remaining amount
  - Estimated months to completion
  - Completion status

### Components & Features

- **UserContext**: Global state management for authenticated user
- **React Router**: Client-side navigation
- **TailwindCSS**: Responsive utility-first styling
- **React Markdown**: Rich text rendering for AI responses
- **Form Handling**: Controlled components with validation
- **API Integration**: Fetch calls to backend endpoints
- **Error Handling**: User-friendly error messages

### Frontend API Integration

**Base URL**: `http://localhost:8000`

```typescript
// Example: Create Goal
const createGoal = async (userId: string, goalData: GoalCreate) => {
  const response = await fetch(`http://localhost:8000/users/${userId}/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(goalData)
  });
  return await response.json();
};

// Example: Send Chat Message
const sendMessage = async (userId: string, message: string) => {
  const response = await fetch('http://localhost:8000/chatbot/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message })
  });
  return await response.json();
};
```

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

## 🗄️ Database Models

### Core Models (UUID-based)

| Model | Fields | Description |
|-------|--------|-------------|
| **User** | `id`, `username`, `created_at`, `income_monthly_kzt` | User account with one-to-one chat |
| **Chat** | `id`, `user_id`, `created_at` | Chat session (auto-created with user) |
| **Message** | `id`, `chat_id`, `role`, `content`, `created_at` | Chat messages (user/assistant) |
| **Transaction** | `id`, `user_id`, `amount`, `transaction_type`, `description`, `transaction_date`, `category`, `balance_after`, `reference_number` | Parsed bank transactions |
| **Goal** | `id`, `user_id`, `title`, `target_amount`, `current_amount`, `monthly_contribution`, `created_at` | Financial goals with progress |

### Extended Models

| Model | Purpose |
|-------|---------|
| **Budget** | User budget planning |
| **BudgetItem** | Individual budget line items |
| **CreditRequest** | Credit/loan applications |
| **DepositRequest** | Deposit product requests |

---

## 🛠️ Technology Stack

### Backend

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.115.0 |
| **ORM** | SQLAlchemy 2.0.23 (async) |
| **Validation** | Pydantic 2.9.0 |
| **Database** | SQLite + aiosqlite |
| **AI** | OpenAI 1.54.0 (GPT-4o-mini) |
| **Parsing** | PyMuPDF 1.23.0, Pandas, openpyxl |
| **RAG** | Custom TF-IDF + cosine similarity |

### Frontend

| Category | Technologies |
|----------|-------------|
| **Framework** | React 19.1.1 |
| **Language** | TypeScript 5.9.3 |
| **Build Tool** | Vite 7.1.7 |
| **Styling** | TailwindCSS 3.4.18 |
| **Routing** | React Router 7.9.4 |
| **Markdown** | React Markdown 10.1.0 |
| **Forms** | @tailwindcss/forms 0.5.10 |

---

## 🧩 AI Chatbot Features

### Available Tools (OpenAI Function Calling)

1. **GetUserSnapshot** - Get complete financial overview
   - Income tracking
   - Transaction history
   - Goal progress
   - Budget status

2. **UpsertIncome** - Update monthly income information

3. **RAGSearch** - Search bank product knowledge base
   - Credit products
   - Deposit options
   - Kopilka (savings)
   - Mortgage information
   - Installment plans (рассрочка)
   - Vakala services

4. **UpdateGoal** - Modify goal progress or parameters

5. **CheckGoalFeasibility** - Analyze if goal is achievable
   - Based on income
   - Current spending patterns
   - Timeline analysis

### RAG Knowledge Base (Auto-loaded)
- **7 Documents** in Kazakh/Russian
- **TF-IDF weighted** search
- **Cosine similarity** ranking
- **Auto-refresh** on startup

---

## 📊 Statement Parser Capabilities

### Supported Formats

| Format | Details |
|--------|---------|
| **CSV** | Auto-detects columns (date, amount, description, category) |
| **Excel** | .xlsx and .xls support |
| **PDF** | Kaspi Bank specialized parser + generic fallback |

### Kaspi Bank PDF Parser
- **Regex extraction** of transaction tables
- **Balance tracking** after each transaction
- **Reference number** capture
- **Date parsing** in multiple formats

### Auto-Categorization
- **Income**: Positive amounts or "income" category
- **Expense**: Negative amounts or "expense" category
- **Custom categories**: Preserved from statement

---

## 🔐 Security & Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults provided)
DATABASE_URL=sqlite+aiosqlite:///./zaman.db
ENVIRONMENT=development
DEBUG=True
```

### CORS Configuration
- Currently allows all origins (`*`)
- **Production**: Update in `main.py` with your frontend URL

---

## 🚦 Development Workflow

### Run in Development Mode
```bash
# Using start script
python start.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/

# API docs
open http://localhost:8000/docs
```

### Database Management
- **Auto-creates** all tables on startup
- **Location**: `./zaman.db`
- **Reset**: Delete `zaman.db` and restart server

---

## 📦 Deployment

### Production Checklist

**Backend:**
- [ ] Set `DEBUG=False` in `.env`
- [ ] Update CORS allowed origins in `main.py`
- [ ] Set production `DATABASE_URL` (PostgreSQL recommended)
- [ ] Secure `OPENAI_API_KEY`
- [ ] Use production ASGI server (Gunicorn)

**Frontend:**
- [ ] Build production bundle: `npm run build`
- [ ] Configure API base URL for production
- [ ] Set up CDN for static assets
- [ ] Enable compression (gzip/brotli)
- [ ] Configure environment-specific builds

### Deploy Backend with Gunicorn
```bash
pip install gunicorn

gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Deploy Frontend

**Option 1: Static Hosting (Vercel/Netlify)**
```bash
cd frontend
npm run build
# Deploy 'dist' folder to Vercel/Netlify
```

**Option 2: Docker (Full Stack)**
**Option 2: Docker (Full Stack)**

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose (Full Stack):**
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite+aiosqlite:///./zaman.db
    volumes:
      - ./zaman.db:/app/zaman.db
      - ./rag:/app/rag

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

Run with:
```bash
docker-compose up -d
```

---

## 🎯 Roadmap & Future Features

**Backend:**
- [ ] WebSocket support for real-time chat streaming
- [ ] User authentication (JWT)
- [ ] PostgreSQL support for production
- [ ] Redis caching for RAG results
- [ ] Async task queue (Celery)
- [ ] Credit score estimation
- [ ] Integration with real bank APIs
- [ ] Voice interaction (Whisper integration)

**Frontend:**
- [ ] Real-time chat updates (WebSocket)
- [ ] Dark mode toggle
- [ ] Multi-language support (EN/KZ/RU)
- [ ] Advanced analytics dashboard
- [ ] Budget visualization charts (Chart.js/Recharts)
- [ ] Transaction filtering and search
- [ ] Export reports (PDF/CSV)
- [ ] Mobile app (React Native)
- [ ] PWA support
- [ ] Notifications system

---

## 📚 Documentation

- **Quick Start**: `QUICKSTART.md`
- **Integration Guide**: `INTEGRATION.md`
- **Chatbot Details**: `CHATBOT_INTEGRATED.md`
- **Parser Guide**: `INTEGRATION_COMPLETE.md`
- **API Docs**: http://localhost:8000/docs

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Team

**Zaman AI Assistant** - Hackathon Project

---

## 🎉 Status

✅ **Production Ready** - All features integrated and tested

**Backend:**
- ✅ Parser: CSV/Excel/PDF support (Kaspi Bank)
- ✅ Chatbot: OpenAI GPT-4 with 5 financial tools
- ✅ RAG: 7 documents auto-loaded with TF-IDF
- ✅ Goals: Advanced tracking with auto-calculations
- ✅ Database: UUID-based SQLite architecture
- ✅ API: Fully documented with Swagger/ReDoc

**Frontend:**
- ✅ React 19 with TypeScript
- ✅ Vite for fast development
- ✅ TailwindCSS responsive design
- ✅ Chat page with message history
- ✅ Goals page with progress tracking
- ✅ User context management
- ✅ Markdown rendering for AI responses

**Ready for hackathon presentation!** 🚀

---

**Made with ❤️ for better financial management**
