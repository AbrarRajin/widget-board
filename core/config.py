"""Application configuration management."""

import os
import json
import logging
from pathlib import Path
from typing import Any
from platformdirs import user_config_dir, user_data_dir, user_log_dir


class Config:
    """Application configuration with platform-aware paths."""
    
    def __init__(self) -> None:
        """Initialize configuration with defaults."""
        self.app_name = "WidgetBoard"
        self.version = "0.1.0"
        
        # Platform-aware directories
        self.config_dir = Path(user_config_dir(self.app_name, ensure_exists=True))
        self.data_dir = Path(user_data_dir(self.app_name, ensure_exists=True))
        self.log_dir = Path(user_log_dir(self.app_name, ensure_exists=True))
        
        # Core paths
        self.database_path = self.data_dir / "app.db"
        self.log_file = self.log_dir / "app.log"
        self.settings_file = self.config_dir / "settings.json"
        
        # Runtime settings
        self.log_level = logging.INFO
        self.theme = "light"
        self.window_width = 1280
        self.window_height = 800
        self.grid_rows = 8
        self.grid_cols = 8
        
        # Development toggles
        self.dev_mode = os.getenv("WIDGETBOARD_DEV", "false").lower() == "true"
        
        # Load user settings if they exist
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from JSON file if it exists."""
        if not self.settings_file.exists():
            return
        
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Apply settings
            self.theme = data.get("theme", self.theme)
            self.window_width = data.get("window_width", self.window_width)
            self.window_height = data.get("window_height", self.window_height)
            
            if data.get("log_level"):
                self.log_level = getattr(logging, data["log_level"], logging.INFO)
        
        except (json.JSONDecodeError, OSError) as e:
            # If settings are corrupt, continue with defaults
            logging.warning("Failed to load settings: %s", e)
    
    def save_settings(self) -> None:
        """Persist current settings to JSON file."""
        data = {
            "theme": self.theme,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "log_level": logging.getLevelName(self.log_level),
        }
        
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logging.error("Failed to save settings: %s", e)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
        
        Returns:
            Configuration value or default.
        """
        return getattr(self, key, default)
