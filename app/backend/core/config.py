from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TriageAI"
    APP_ENV: str = "development"
    DEBUG: bool = False
    AUTO_CREATE_TABLES: bool = False
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    SESSION_TTL_MINUTES: int = Field(default=60, ge=5, le=1440)
    PUBLIC_DEMO_ENABLED: bool = True
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=0, ge=0, le=10)
    DATABASE_URL: str = "sqlite:///./triageai.db"
    MODEL_REGISTRY_DIR: str = "model_registry/esi_345_lightgbm_v2"
    MODEL_DEPLOYMENT_CONFIG: str = (
        "model_registry/esi_345_lightgbm_v2/esi_345_deployment_config.json"
    )
    MODEL_PATH: str = "model_registry/esi_345_lightgbm_v2/esi_345_lightgbm_v2_model.txt"
    PREPROCESSOR_PATH: str = (
        "model_registry/esi_345_lightgbm_v2/"
        "esi_345_lightgbm_v2_preprocessing_artifacts.joblib"
    )
    THRESHOLDS_PATH: str = (
        "model_registry/esi_345_lightgbm_v2/"
        "esi_345_lightgbm_v2_threshold_config.json"
    )
    FEATURE_SCHEMA_PATH: str = (
        "model_registry/esi_345_lightgbm_v2/"
        "esi_345_lightgbm_v2_feature_list.json"
    )
    MODEL_METADATA_PATH: str = (
        "model_registry/esi_345_lightgbm_v2/esi_345_deployment_config.json"
    )
    LABEL_MAPPING_PATH: str = "model_registry/esi_345_lightgbm_v2/esi_345_label_mapping.json"
    REPORT_OUTPUT_DIR: str = "reports/generated"
    REPORT_STORAGE_BACKEND: Literal["local", "gcs"] = "local"
    REPORT_GCS_BUCKET: str = ""
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_deployment(self) -> "Settings":
        if self.REPORT_STORAGE_BACKEND == "gcs" and not self.REPORT_GCS_BUCKET:
            raise ValueError("REPORT_GCS_BUCKET is required for GCS report storage")
        if self.APP_ENV.lower() in {"production", "staging"}:
            if self.DEBUG or self.AUTO_CREATE_TABLES:
                raise ValueError("Deployment requires DEBUG=false and AUTO_CREATE_TABLES=false")
            if not self.DATABASE_URL.startswith("postgresql+psycopg://"):
                raise ValueError("Deployment requires PostgreSQL with the psycopg driver")
            if self.REPORT_STORAGE_BACKEND != "gcs":
                raise ValueError("Deployment requires durable GCS report storage")
            if not self.CORS_ALLOWED_ORIGINS or any(
                origin == "*" or not origin.startswith("https://")
                for origin in self.CORS_ALLOWED_ORIGINS
            ):
                raise ValueError("Deployment requires explicit HTTPS frontend origins")
        return self

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value


settings = Settings()
