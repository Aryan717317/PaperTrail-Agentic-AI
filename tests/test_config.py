from app.config import Settings


def test_openrouter_and_local_embedding_defaults():
    settings = Settings(openrouter_api_key="test-key")
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.openrouter_model == "openrouter/free"
    assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
