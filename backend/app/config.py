from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Carrgo"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./carrgo.db"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Vapi — get these from https://dashboard.vapi.ai
    vapi_api_key: str = ""  # Required for real calls
    vapi_base_url: str = "https://api.vapi.ai"
    vapi_phone_number_id: str = ""  # Broker's outbound phone number ID from Vapi dashboard
    vapi_webhook_secret: str = ""  # Optional: to verify webhook signatures

    # Voice AI model config
    voice_model_provider: str = "openai"  # LLM provider Vapi uses for conversation
    voice_model: str = "gpt-4o-mini"  # LLM model for negotiation
    voice_provider: str = "11labs"  # TTS provider
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs voice ID (Rachel)

    # Outreach
    max_parallel_calls: int = 10
    default_call_timeout_secs: int = 120

    # Webhook — the public URL where Vapi sends call events
    # For local dev, use ngrok: ngrok http 8000 → then set this to the ngrok URL
    webhook_base_url: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
