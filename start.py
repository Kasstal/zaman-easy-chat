"""
Quick start script to run the Zaman AI Assistant API
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Zaman AI Assistant API")
    print("=" * 60)
    print("\nAPI Documentation will be available at:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
