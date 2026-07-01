from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TriageAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./triageai.db"
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MODEL_PATH: str = "model_artifacts/esi_345_lightgbm_v2_threshold.txt"
    PREPROCESSOR_PATH: str = ""
    THRESHOLDS_PATH: str = "model_artifacts/thresholds.json"
    FEATURE_SCHEMA_PATH: str = "model_artifacts/feature_schema.json"
    MODEL_METADATA_PATH: str = "model_artifacts/model_metadata.json"
    REPORT_OUTPUT_DIR: str = "reports/generated"
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value


settings = Settings()
