# Zaman AI Assistant

AI Banking Assistant backend with FastAPI, SQLAlchemy, and SQLite.

## Features

- **User Management**: Create users with automatic chat creation
- **Chatbot Service**: Chat interaction with message history
- **Statement Parser**: Upload bank statements and extract transactions
- **Goal Tracking**: Create and track financial goals
- **Clean Architecture**: Modular structure with separation of concerns

## Project Structure

```
zaman-easy-chat/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── crud/            # Database operations
│   ├── routers/         # API endpoints
│   ├── config.py        # Configuration
│   └── database.py      # Database setup
├── main.py              # FastAPI application
├── requirements.txt     # Dependencies
└── .env.example         # Environment variables template
```

## Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Users
- `POST /users/` - Create a new user
- `GET /users/{user_id}` - Get user details
- `POST /users/{user_id}/goals` - Create a goal
- `GET /users/{user_id}/goals` - Get user's goals
- `PUT /users/goals/{goal_id}` - Update goal progress

### Chatbot
- `POST /chatbot/chat` - Send message and get AI response
- `GET /chatbot/messages/{user_id}` - Get chat history

### Parser
- `POST /parser/upload-statement/{user_id}` - Upload bank statement
- `GET /parser/transactions/{user_id}` - Get user's transactions

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
