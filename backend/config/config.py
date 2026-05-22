from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Main application settings"""
    
    # Database (SENSITIVE - No defaults)
    database_url: str
    sql_echo: bool = False
    
    # OpenAI / LLM (API keys are SENSITIVE)
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.7
    llm_timeout: int = 30
    
    # Google OAuth (SENSITIVE credentials - No defaults)
    google_client_id: str
    google_client_secret: str
    google_project_id: str
    google_redirect_uri: str
    google_token_refresh: Optional[str] = None
    google_scopes: str
    
    # Encryption (SENSITIVE - No defaults)
    # Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
    encryption_key: str

    # Google Sheets — ID from spreadsheet URL (docs.google.com/spreadsheets/d/{ID}/edit)
    google_sheet_id: str = ""
    
    # App Settings
    app_name: str = "AssistAI Desktop"
    app_version: str = "1.0.0"
    app_debug: bool = False
    app_log_level: str = "INFO"
    app_data_dir: str = str(Path(__file__).parent.parent / "data")
    app_window_width: int = 1200
    app_window_height: int = 800
    app_theme: str = "light"
    app_auto_save: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-create data directory
        Path(self.app_data_dir).mkdir(parents=True, exist_ok=True)
    
    @property
    def google_scopes_list(self) -> list:
        """Return scopes as list"""
        return [s.strip() for s in self.google_scopes.split(",")]
    
    @property
    def config_as_dict(self) -> dict:
        """Return config as dictionary (for backward compatibility)"""
        return {
            "app": {
                "name": self.app_name,
                "version": self.app_version,
                "debug": self.app_debug,
                "log_level": self.app_log_level,
                "data_dir": self.app_data_dir,
                "window_width": self.app_window_width,
                "window_height": self.app_window_height,
                "theme": self.app_theme,
                "auto_save": self.app_auto_save,
            },
            "google": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "project_id": self.google_project_id,
                "scopes": self.google_scopes_list,
            },
            "llm": {
                "model": self.llm_model,
                "api_key": self.llm_api_key,
                "max_tokens": self.llm_max_tokens,
                "temperature": self.llm_temperature,
                "timeout": self.llm_timeout,
            },
        }


# Global settings instance
settings = Settings()
