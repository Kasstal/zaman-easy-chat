# Quick Start Guide

## Setup and Run

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start the server**:
```bash
python start.py
```

The server will start on http://localhost:8000

3. **Access API documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Test the API

Create a test user:
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user"}'
```

Upload a bank statement (replace {user_id} with the returned user ID):
```bash
curl -X POST "http://localhost:8000/parser/upload-statement/{user_id}" \
  -F "file=@path/to/your/statement.pdf"
```

## Database

The SQLite database (`zaman.db`) is created automatically when you start the server for the first time.

## Parser Integration

The parser from `to integrate/statement_parser.py` is now fully integrated and supports:
- ✅ CSV files
- ✅ Excel files (.xlsx, .xls)
- ✅ PDF files (Kaspi Bank and generic formats)

The parser automatically:
- Detects file format
- Extracts transactions
- Categorizes as income/expense
- Handles multiple date formats
- Supports multiple banks

## Project Status

✅ Database models created
✅ API endpoints ready
✅ Statement parser integrated
⏳ Chatbot logic (placeholder - ready for integration)

See `INTEGRATION.md` for chatbot integration guide.
