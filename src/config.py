"""Application configuration loaded from environment variables."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Document Analysis System"
    app_version: str = "0.1.0"
    debug: bool = True

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    upload_dir: Path = base_dir / "data" / "raw"
    export_dir: Path = base_dir / "data" / "exports"

    # Database
    database_url: str = "sqlite:///./documents.db"

    # ML
    ner_model: str = "Davlan/bert-base-multilingual-cased-ner-hrl"

    # Files
    max_file_size_mb: int = 50
    supported_formats: set[str] = {".pdf", ".docx", ".xlsx"}

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()

# Ensure required directories exist
for _dir in (settings.upload_dir, settings.export_dir):
    _dir.mkdir(parents=True, exist_ok=True)