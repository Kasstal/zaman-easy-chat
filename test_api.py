"""
Simple test script to verify the API setup
Run after starting the server: uvicorn main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.json()}")
    return response.status_code == 200


def test_create_user():
    """Test user creation"""
    data = {"username": "test_user"}
    response = requests.post(f"{BASE_URL}/users/", json=data)
    print(f"Create User: {response.json()}")
    return response.json()


def test_chat(user_id):
    """Test chat endpoint"""
    data = {
        "user_id": user_id,
        "message": "Hello, I need help with my finances"
    }
    response = requests.post(f"{BASE_URL}/chatbot/chat", json=data)
    print(f"Chat Response: {response.json()}")
    return response.json()


def test_get_messages(user_id):
    """Test getting chat history"""
    response = requests.get(f"{BASE_URL}/chatbot/messages/{user_id}")
    print(f"Chat History: {response.json()}")
    return response.json()


def test_create_goal(user_id):
    """Test goal creation"""
    data = {
        "title": "Save for vacation",
        "target_amount": 5000.0
    }
    response = requests.post(f"{BASE_URL}/users/{user_id}/goals", json=data)
    print(f"Create Goal: {response.json()}")
    return response.json()


def test_upload_statement(user_id):
    """Test statement upload"""
    # Create a dummy file
    files = {"file": ("statement.txt", b"dummy statement content", "text/plain")}
    response = requests.post(
        f"{BASE_URL}/parser/upload-statement/{user_id}",
        files=files
    )
    print(f"Upload Statement: {response.json()}")
    return response.json()


def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("Testing Zaman AI Assistant API")
    print("=" * 50)
    
    try:
        # Test health
        print("\n1. Testing Health Check...")
        test_health()
        
        # Create user
        print("\n2. Creating User...")
        user = test_create_user()
        user_id = user["id"]
        
        # Test chat
        print("\n3. Testing Chat...")
        test_chat(user_id)
        
        # Get messages
        print("\n4. Getting Chat History...")
        test_get_messages(user_id)
        
        # Create goal
        print("\n5. Creating Goal...")
        test_create_goal(user_id)
        
        # Upload statement
        print("\n6. Uploading Statement...")
        test_upload_statement(user_id)
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the server is running: uvicorn main:app --reload")


if __name__ == "__main__":
    run_tests()
