"""Settings loaded from environment variables or a .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "taxlens"
    postgres_password: str = "taxlens"
    postgres_db: str = "taxlens"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Where downloaded PDFs are stored. Git-ignored.
    data_dir: Path = Path("data")

    # Crawler politeness. Identify the project honestly, without personal details.
    user_agent: str = "TaxLens-portfolio-crawler/0.1"
    request_delay_seconds: float = 2.0

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
