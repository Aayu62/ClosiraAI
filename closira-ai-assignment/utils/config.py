import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration management."""

    def __init__(self):
        self.openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
        self.model: str = os.getenv("MODEL", "deepseek/deepseek-chat")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.base_url: str = "https://openrouter.ai/api/v1"
        self.project_root: Path = Path(__file__).parent.parent
        self.data_dir: Path = self.project_root / "data"
        self.prompts_dir: Path = self.project_root / "prompts"
        self.logs_dir: Path = self.project_root / "logs"
        self.sessions_dir: Path = self.project_root / "sessions"
        self.confidence_threshold: float = 0.70
        self.max_retries: int = 2

    def get_knowledge_base_path(self) -> Path:
        """Get knowledge base file path."""
        return self.data_dir / "service_knowledge.json"

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
        self.logs_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        return True

    def get_sop_path(self) -> Path:
        """Get SOP data file path."""
        return self.data_dir / "sop.json"

    def get_leads_path(self) -> Path:
        """Get leads data file path."""
        return self.data_dir / "leads.json"

    def get_prompt_path(self, prompt_name: str) -> Path:
        """Get prompt file path."""
        return self.prompts_dir / f"{prompt_name}.txt"
