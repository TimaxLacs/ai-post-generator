# tests/conftest.py
import pytest

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("TG_BOT_TOKEN", "test_tg_token")
    monkeypatch.setenv("TG_CHANNEL_ID", "test_tg_id")
    monkeypatch.setenv("VK_ACCESS_TOKEN", "test_vk_token")
    monkeypatch.setenv("VK_GROUP_ID", "test_vk_id")
