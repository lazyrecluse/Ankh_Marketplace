from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app.main import app

client = TestClient(app)

@patch("backend.app.ai_helper.generate_ai_response")
def test_ai_chat_endpoint_mocked(mock_generate):
    # Setup mock response
    mock_generate.return_value = {
        "response": "Based on your temperate climate preference and sensitive skin, I recommend using our organic linen (id: linen-1) which is hypoallergenic.",
        "recommended_products": ["linen-1"]
    }
    
    chat_payload = {
        "message": "I live in a temperate climate and need hypoallergenic fabrics.",
        "chat_history": []
    }
    
    res = client.post("/api/ai/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "linen-1" in data["recommended_products"]
    mock_generate.assert_called_once()

if __name__ == "__main__":
    import sys
    print("Running AI assistant tests...")
    try:
        test_ai_chat_endpoint_mocked()
        print("[PASS] test_ai_chat_endpoint_mocked")
        print("All AI assistant tests passed successfully!")
    except Exception as e:
        print(f"[FAIL] AI assistant tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

