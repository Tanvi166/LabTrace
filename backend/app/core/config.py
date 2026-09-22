import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = str(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    PROJECT_NAME: str = "LabTrace"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "super-secret-key-change-in-production-labtrace-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./labtrace.db"
    AZURE_SQL_ENABLED: bool = True
    AZURE_SQL_SERVER: str = "labtrace-sql-3118.database.windows.net"
    AZURE_SQL_DATABASE: str = "labtrace-db"
    AZURE_SQL_DRIVER: str = "ODBC Driver 18 for SQL Server"
    AZURE_SQL_TOKEN_SCOPE: str = "https://database.windows.net/.default"

    @property
    def database_url(self) -> str:
        """Select Azure SQL only when explicitly enabled; SQLite remains default."""
        if not self.AZURE_SQL_ENABLED:
            return self.DATABASE_URL
        driver = quote_plus(self.AZURE_SQL_DRIVER)
        return (
            f"mssql+pyodbc://@{self.AZURE_SQL_SERVER}:1433/{self.AZURE_SQL_DATABASE}"
            f"?driver={driver}&Encrypt=yes&TrustServerCertificate=no"
        )
    
    # Storage
    STORAGE_PROVIDER: str = "local"  # "local" or "azure"
    LOCAL_STORAGE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "storage")
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # Azure Blob Storage. The connection string is for local development only;
    # a later security phase will replace it with Managed Identity/RBAC.
    AZURE_STORAGE_ACCOUNT_NAME: str = "labtracefiles3118"
    AZURE_STORAGE_ACCOUNT_URL: Optional[str] = None
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: str = "research-data"
    
    # Azure OpenAI / OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = "gpt-4o"
    KNOWLEDGE_PROVIDER: str = "local"
    LOCAL_KNOWLEDGE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge")
    EMBEDDING_DIMENSIONS: int = 64
    AZURE_AI_SEARCH_ENDPOINT: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_AI_SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT"),
    )
    AZURE_AI_SEARCH_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_AI_SEARCH_KEY", "AZURE_SEARCH_KEY"),
    )
    AZURE_AI_SEARCH_INDEX_NAME: str = Field(
        default="rag-1789840438987",
        validation_alias=AliasChoices("AZURE_AI_SEARCH_INDEX_NAME", "AZURE_SEARCH_INDEX"),
    )
    AZURE_AI_SEARCH_VECTOR_FIELD: str = Field(
        default="text_vector",
        validation_alias=AliasChoices("AZURE_AI_SEARCH_VECTOR_FIELD", "AZURE_SEARCH_VECTOR_FIELD"),
    )
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Optional[str] = None
    AZURE_FOUNDRY_PROJECT_ENDPOINT: Optional[str] = None
    # Agent APIs require the project-scoped endpoint, unlike the OpenAI v1 model endpoint.
    AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT: Optional[str] = None
    AZURE_FOUNDRY_AGENT_NAME: Optional[str] = None
    # Pin the API to the smoke-tested immutable agent version.  A mismatch is
    # rejected rather than silently sending a request to a newer version.
    AZURE_FOUNDRY_AGENT_VERSION: str = "3"
    AZURE_FOUNDRY_SEARCH_CONNECTION_NAME: Optional[str] = None
    AZURE_FOUNDRY_API_KEY: Optional[str] = None
    AZURE_FOUNDRY_MODEL: Optional[str] = None
    AZURE_FOUNDRY_DEPLOYMENT: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AUTH_PROVIDER: str = "local"
    APPLICATIONINSIGHTS_CONNECTION_STRING: Optional[str] = None
    
    # Azure Entra ID / AD Configuration
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
