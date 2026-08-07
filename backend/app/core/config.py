from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fitness:fitness@localhost:5432/fitness_coach"
    environment: str = "development"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"


settings = Settings()
