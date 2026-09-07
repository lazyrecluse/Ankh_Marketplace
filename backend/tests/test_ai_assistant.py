from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import ai_helper, models
from backend.app.database import SessionLocal

client = TestClient(app)


@patch("backend.app.ai_helper.generate_ai_response")
def test_ai_chat_endpoint_mocked(mock_generate):
    mock_generate.return_value = {
        "response": "Based on your temperate climate preference and sensitive skin, I recommend using our organic linen (id: linen-1) which is hypoallergenic.",
        "recommended_products": ["linen-1"],
        "suggested_filters": {"category": "linen", "climate": "Temperate", "sensitive_skin": True}
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
    assert data["suggested_filters"]["category"] == "linen"
    assert data["suggested_filters"]["sensitive_skin"] is True
    mock_generate.assert_called_once()


@patch("backend.app.ai_helper.generate_ai_response")
def test_ai_chat_rate_limit_429(mock_generate):
    mock_generate.side_effect = ai_helper.AIRateLimitError("Gemini rate limit exceeded.")
    res = client.post("/api/ai/chat", json={"message": "hello", "chat_history": []})
    assert res.status_code == 429
    assert "rate limit" in res.json()["detail"].lower()


@patch("backend.app.ai_helper.generate_ai_response")
def test_ai_chat_disabled_503(mock_generate):
    mock_generate.side_effect = ai_helper.AIDisabledError("AI is disabled.")
    res = client.post("/api/ai/chat", json={"message": "hello", "chat_history": []})
    assert res.status_code == 503
    assert "disabled" in res.json()["detail"].lower()


def test_extract_json_metadata():
    text = (
        "Here is my recommendation for your hot climate:\n\n"
        "- Linen is great.\n\n"
        "```json\n"
        '{\n  "recommended_products": ["linen-1", "cotton-2"],\n'
        '  "suggested_filters": {"category": "linen", "climate": "Tropical"}\n}\n'
        "```"
    )
    clean_text, rec_ids, filters = ai_helper._extract_json_metadata(text)
    assert "Here is my recommendation" in clean_text
    assert "```json" not in clean_text
    assert rec_ids == ["linen-1", "cotton-2"]
    assert filters == {"category": "linen", "climate": "Tropical"}


def test_rag_database_retrieval():
    db = SessionLocal()
    try:
        # Query with sensitive skin keywords
        products, buyer_ctx = ai_helper.retrieve_pertinent_context(
            db, "I have sensitive skin and need hypoallergenic fabric for eczema"
        )
        assert isinstance(products, list)
        assert len(products) > 0
        # The highest scored product should be hypoallergenic
        assert products[0]["is_hypoallergenic"] is True
    finally:
        db.close()


@patch("os.getenv")
def test_generate_ai_response_with_gemini_mock(mock_getenv):
    def fake_getenv(key, default=None):
        if key == "GEMINI_API_KEY":
            return "fake-gemini-key"
        if key == "ANKH_AI_ENABLED":
            return "true"
        return default
    mock_getenv.side_effect = fake_getenv

    db = SessionLocal()
    try:
        # Mock google.genai inside generate_ai_response
        fake_response = MagicMock()
        fake_response.text = (
            "I recommend organic linen (id: linen-1) for warm weather.\n\n"
            "```json\n"
            '{\n  "recommended_products": ["linen-1"],\n'
            '  "suggested_filters": {"category": "linen"}\n}\n'
            "```"
        )

        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = fake_response

        with patch("google.genai.Client", return_value=fake_client):
            result = ai_helper.generate_ai_response(
                db=db,
                message="Recommend something for warm weather",
                chat_history=[]
            )
            assert "response" in result
            assert "suggested_filters" in result
            assert result["suggested_filters"] == {"category": "linen"}
    finally:
        db.close()

