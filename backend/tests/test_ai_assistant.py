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


@patch("os.getenv")
def test_env_sanitization_strips_newlines(mock_getenv):
    def fake_getenv(key, default=None):
        if key == "GROQ_API_KEY":
            return "  my-groq-key\n"
        if key == "GROQ_MODEL":
            return "llama-3.3-70b-versatile\n"
        if key == "GEMINI_API_KEY":
            return "  my-secret-key\n"
        if key == "GEMINI_MODEL":
            return "gemini-3.6-flash\n"
        return default
    mock_getenv.side_effect = fake_getenv

    assert ai_helper.get_groq_api_key() == "my-groq-key"
    assert ai_helper.get_groq_model() == "llama-3.3-70b-versatile"
    assert ai_helper.get_gemini_api_key() == "my-secret-key"
    assert ai_helper.get_gemini_model() == "gemini-3.6-flash"


@patch("backend.app.ai_helper.call_groq_api")
@patch("os.getenv")
def test_generate_ai_response_with_groq_mock(mock_getenv, mock_groq):
    def fake_getenv(key, default=None):
        if key == "GROQ_API_KEY":
            return "fake-groq-key"
        if key == "ANKH_AI_ENABLED":
            return "true"
        return default
    mock_getenv.side_effect = fake_getenv

    mock_groq.return_value = (
        "Groq recommends Belgian Linen (id: linen-belgian-1) for hot weather.\n\n"
        "```json\n"
        '{\n  "recommended_products": ["linen-belgian-1"],\n'
        '  "suggested_filters": {"category": "linen", "climate": "Tropical"}\n}\n'
        "```"
    )

    db = SessionLocal()
    try:
        result = ai_helper.generate_ai_response(
            db=db,
            message="Recommend something for hot weather",
            chat_history=[]
        )
        assert "Groq recommends" in result["response"]
        assert "linen-belgian-1" in result["recommended_products"]
        assert result["suggested_filters"]["category"] == "linen"
        mock_groq.assert_called_once()
    finally:
        db.close()


def test_generate_ai_response_offline_heuristic_fallback():
    """Verify local development works with 100% uptime without any API keys."""
    db = SessionLocal()
    try:
        # Greeting test
        greet_res = ai_helper.generate_ai_response(db, "hello", [])
        assert "Welcome to the Ankh Marketplace Textile Assistant" in greet_res["response"]

        # Product recommendation test
        spec_res = ai_helper.generate_ai_response(db, "I need breathable linen for hot tropical climate", [])
        assert "top fabric recommendations" in spec_res["response"]
        assert len(spec_res["recommended_products"]) > 0
        assert spec_res["suggested_filters"]["category"] == "linen"
    finally:
        db.close()

