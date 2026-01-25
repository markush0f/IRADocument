from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IRADocument API"
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_backup_count: int = 30

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b-instruct"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="IRA_")


settings = Settings()
