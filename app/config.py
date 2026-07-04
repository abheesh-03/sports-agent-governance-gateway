"""Application configuration.

Loads settings from environment variables (optionally via a local .env file).
No paid API keys are required for version 1.
"""
import os

from dotenv import load_dotenv

# Load variables from a .env file if present. Environment variables that are
# already set always take precedence.
load_dotenv()


class Settings:
    """Simple settings container populated from the environment."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./sports_agent_gateway.db"
    )
    APP_NAME: str = os.getenv("APP_NAME", "Sports Agent Governance Gateway")
    DEFAULT_ORG: str = os.getenv("DEFAULT_ORG", "Northstar Athletics")
    SERVICE_NAME: str = "sports-agent-governance-gateway"


settings = Settings()
