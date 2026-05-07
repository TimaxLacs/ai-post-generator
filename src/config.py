from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    tg_bot_token: str = ""
    tg_channel_id: str = ""
    vk_access_token: str = ""
    vk_group_id: str = ""
    
    gen_model: str = "google/gemini-2.0-flash-lite-preview-02-05:free"
    mod_model: str = "google/gemini-2.0-flash-lite-preview-02-05:free"
    
    gen_sys_prompt: str = "You are a professional social media manager. Write an engaging post based on the context. STRICT RULE: NO markdown formatting. Length strictly under 900 chars."
    mod_sys_prompt: str = "You are a strict editor. Reply EXACTLY with 'APPROVED' if the post is perfect. Otherwise, write constructive feedback. Ensure no markdown and length < 900 chars."
    
    post_interval_seconds: int = 600

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
