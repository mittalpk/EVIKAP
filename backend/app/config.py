"""Application settings loaded from environment variables."""
from __future__ import annotations

import os
import logging
from typing import List
from pydantic import SecretStr, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore", 
        case_sensitive=False
    )

    # Azure AD
    azure_tenant_id: str = ""
    azure_client_id: str = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # Microsoft's well-known public Azure CLI client ID
    skip_auth: bool = True  # Temporary bypass until Frontend MSAL integration is built

    # CORS
    allowed_origins: List[str] = []

    # LLM
    openai_api_key: SecretStr = SecretStr("")
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"

    # Databases / Integrations
    confluence_base_url: str = ""
    confluence_api_token: SecretStr = SecretStr("")
    database_url: str = "sqlite:///./vigilrag.db"
    
    # GitHub Integration
    github_pat: SecretStr = Field(default=SecretStr(""), alias="GITHUB_PAT")
    
    # Azure Storage Integration
    azure_storage_connection_string: SecretStr = Field(default=SecretStr(""), alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_wiki_container: str = Field(default="vigilrag-wiki", alias="AZURE_WIKI_CONTAINER")

    # Internal Security
    internal_api_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"), 
        validation_alias=AliasChoices("INTERNAL_API_KEY", "internal-api-key", "X-Internal-API-Key")
    )

    # Admin Credentials (Explicitly mapped to Key Vault env vars)
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: SecretStr = Field(
        default=SecretStr("change-me-in-production"), 
        alias="ADMIN_PASSWORD"
    )

    # Secret key for JWT
    secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        alias="SECRET_KEY"
    )

    # Demo Mode (opt-in simulated data)
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"✓ Settings initialized: INTERNAL_API_KEY length = {len(self.internal_api_key.get_secret_value())}")
        logger.info(f"  BACKEND_URL env var: {os.getenv('BACKEND_URL', 'NOT SET')}")
        logger.info(f"  AGENT_SERVICE_URL env var: {os.getenv('AGENT_SERVICE_URL', 'NOT SET')}")
        logger.info(f"  DEMO_MODE: {self.demo_mode}")



settings = Settings()
