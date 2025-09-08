"""
CONFIG.PY - Configuration Management System
==========================================
Mục đích: Quản lý tất cả configuration settings cho application
Chức năng:
- Load settings từ JSON files và environment variables
- Validate configuration values
- Provide default settings
- Environment-specific configs (dev, prod)
- Runtime configuration updates
- Secure handling của API keys và secrets
- Configuration backup và restore
Dependencies: None (base utility)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class Environment(Enum):
    """Môi trường chạy application"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class GoogleConfig:
    """Google Services Configuration"""
    credentials_file: str
    scopes: List[str]
    token_file: str
    calendar_id: Optional[str] = None
    sheets_folder_id: Optional[str] = None

@dataclass
class LLMConfig:
    """LLM Configuration"""
    model_name: str
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30

@dataclass
class AppConfig:
    """Desktop Application Configuration"""
    app_name: str
    version: str
    debug: bool
    log_level: str
    data_dir: str
    # Desktop specific
    window_width: int = 1200
    window_height: int = 800
    theme: str = "light"  # light, dark
    auto_save: bool = True

class ConfigManager:
    """Quản lý configuration cho Desktop LLM Agent"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent
        self.config_file = config_file or self.project_root / "settings.json"
        self.credentials_file = self.project_root / "credentials.json"
        self.token_file = self.project_root / "token.json"
        
        # Desktop app luôn development mode
        self.environment = Environment.DEVELOPMENT
        
        # Load configuration
        self._config_data = self._load_config()
        self._validate_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for desktop app"""
        default_config = {
            "app": {
                "name": "AssistAI Desktop",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
                "data_dir": str(self.project_root / "data"),
                "window_width": 1200,
                "window_height": 800,
                "theme": "light",
                "auto_save": True
            },
            "google": {
                "credentials_file": str(self.credentials_file),
                "token_file": str(self.token_file),
                "scopes": [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/calendar"
                ],
                "calendar_id": None,
                "sheets_folder_id": None
            },
            "llm": {
                "model_name": "gpt-3.5-turbo",
                "api_key": None,
                "max_tokens": 1000,
                "temperature": 0.7,
                "timeout": 30
            }
        }
        
        # Load user settings nếu có
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Deep merge với default config
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                logging.warning(f"Không thể load settings file: {e}")
        
        # Không cần environment variables cho desktop app
        return default_config
    
    def _deep_merge(self, default_dict: Dict, update_dict: Dict) -> None:
        """Deep merge hai dictionaries"""
        for key, value in update_dict.items():
            if key in default_dict and isinstance(default_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(default_dict[key], value)
            else:
                default_dict[key] = value
    
    def _validate_config(self) -> None:
        """Validate configuration settings"""
        errors = []
        
        # Kiểm tra Google credentials (optional cho desktop)
        if not self.credentials_file.exists():
            logging.info(f"Google credentials file chưa có: {self.credentials_file}")
            logging.info("Bạn cần thêm credentials.json để sử dụng Google Services")
        
        # Tạo data directory nếu chưa có
        data_dir = Path(self._config_data["app"]["data_dir"])
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"Đã tạo data directory: {data_dir}")
            except Exception as e:
                errors.append(f"Không thể tạo data directory: {e}")
        
        # Kiểm tra window size hợp lệ
        if self._config_data["app"]["window_width"] < 800:
            self._config_data["app"]["window_width"] = 800
        if self._config_data["app"]["window_height"] < 600:
            self._config_data["app"]["window_height"] = 600
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_level = getattr(logging, self._config_data["app"]["log_level"].upper())
        
        # Tạo logs directory
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(logs_dir / "app.log", encoding='utf-8')
            ]
        )
        
        # Tắt debug logs của các thư viện bên ngoài
        logging.getLogger("google").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    @property
    def google(self) -> GoogleConfig:
        """Google services configuration"""
        config = self._config_data["google"]
        return GoogleConfig(**config)
    
    @property
    def llm(self) -> LLMConfig:
        """LLM configuration"""
        config = self._config_data["llm"]
        return LLMConfig(**config)
    
    @property
    def app(self) -> AppConfig:
        """Application configuration"""
        config = self._config_data["app"]
        return AppConfig(**config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value bằng dot notation (e.g., 'google.scopes')"""
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value bằng dot notation"""
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        # Auto save nếu được bật
        if self.app.auto_save:
            self.save_config()
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """Lưu configuration ra file"""
        target_file = Path(file_path) if file_path else self.config_file
        
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Settings saved to {target_file}")
        except Exception as e:
            logging.error(f"Không thể lưu settings: {e}")
            raise
    
    def backup_config(self) -> str:
        """Backup configuration file"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.project_root / f"settings_backup_{timestamp}.json"
        
        if self.config_file.exists():
            import shutil
            shutil.copy2(self.config_file, backup_file)
            logging.info(f"Settings backed up to {backup_file}")
            return str(backup_file)
        return ""
    
    def reset_to_defaults(self) -> None:
        """Reset configuration về mặc định"""
        if self.config_file.exists():
            backup = self.backup_config()
            logging.info(f"Current settings backed up to {backup}")
        
        # Reload với default values
        self._config_data = self._load_config()
        self.save_config()
        logging.info("Settings reset to defaults")
    
    def is_google_authenticated(self) -> bool:
        """Kiểm tra xem đã authenticate với Google chưa"""
        return self.token_file.exists() and self.credentials_file.exists()
    
    def clear_google_token(self) -> None:
        """Xóa Google token để re-authenticate"""
        if self.token_file.exists():
            self.token_file.unlink()
            logging.info("Google token cleared - cần authenticate lại")
    
    def has_google_credentials(self) -> bool:
        """Kiểm tra có file credentials.json không"""
        return self.credentials_file.exists()
    
    def has_llm_api_key(self) -> bool:
        """Kiểm tra có API key cho LLM không"""
        return bool(self.llm.api_key and self.llm.api_key.strip())
    
    def get_status(self) -> Dict[str, bool]:
        """Lấy trạng thái setup của app"""
        return {
            "google_credentials": self.has_google_credentials(),
            "google_authenticated": self.is_google_authenticated(),
            "llm_api_key": self.has_llm_api_key(),
            "data_directory": Path(self.app.data_dir).exists()
        }

# Global config instance
config = ConfigManager()

# Convenience functions
def get_config() -> ConfigManager:
    """Get global config instance"""
    return config

def reload_config() -> None:
    """Reload configuration"""
    global config
    config = ConfigManager()

def setup_first_run() -> bool:
    """Setup wizard cho lần đầu chạy app"""
    config = get_config()
    status = config.get_status()
    
    # Kiểm tra xem cần setup không
    if all(status.values()):
        return True
    
    logging.info("First run detected - some setup required:")
    for key, value in status.items():
        status_text = "✅" if value else "❌"
        logging.info(f"  {status_text} {key}")
    
    return False