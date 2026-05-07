# tests/conftest.py
import os
import pytest

# Set environment variables before any modules are imported to ensure pydantic-settings picks them up
os.environ["OPENROUTER_API_KEY"] = "test_key"
os.environ["TG_BOT_TOKEN"] = "test_tg_token"
os.environ["TG_CHANNEL_ID"] = "test_tg_id"
os.environ["VK_ACCESS_TOKEN"] = "test_vk_token"
os.environ["VK_GROUP_ID"] = "test_vk_id"

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("TG_BOT_TOKEN", "test_tg_token")
    monkeypatch.setenv("TG_CHANNEL_ID", "test_tg_id")
    monkeypatch.setenv("VK_ACCESS_TOKEN", "test_vk_token")
    monkeypatch.setenv("VK_GROUP_ID", "test_vk_id")
