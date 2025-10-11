"""Theme management for application styling."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages application themes and styling."""
    
    def __init__(self, themes_dir: Optional[Path] = None) -> None:
        """Initialize theme manager.
        
        Args:
            themes_dir: Directory containing theme JSON files.
                       Defaults to 'themes/' relative to project root.
        """
        if themes_dir is None:
            # Default to themes directory in project root
            themes_dir = Path(__file__).parent.parent / "themes"
        
        self.themes_dir = themes_dir
        self.current_theme_name = "light"
        self.themes: Dict[str, Dict[str, Any]] = {}
        
        # Load available themes
        self._load_themes()
    
    def _load_themes(self) -> None:
        """Load all theme JSON files from themes directory."""
        if not self.themes_dir.exists():
            logger.warning("Themes directory not found: %s", self.themes_dir)
            self._create_default_themes()
            return
        
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, "r", encoding="utf-8") as f:
                    theme_data = json.load(f)
                
                theme_name = theme_file.stem
                self.themes[theme_name] = theme_data
                logger.info("Loaded theme: %s", theme_name)
            
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load theme %s: %s", theme_file, e)
        
        if not self.themes:
            logger.warning("No themes loaded, using defaults")
            self._create_default_themes()
    
    def _create_default_themes(self) -> None:
        """Create default light and dark themes."""
        self.themes["light"] = {
            "name": "Light",
            "colors": {
                "background": "#FFFFFF",
                "surface": "#F5F5F5",
                "primary": "#2196F3",
                "secondary": "#757575",
                "text": "#212121",
                "text_secondary": "#757575",
                "border": "#E0E0E0",
                "error": "#F44336",
                "success": "#4CAF50",
                "warning": "#FF9800"
            }
        }
        
        self.themes["dark"] = {
            "name": "Dark",
            "colors": {
                "background": "#121212",
                "surface": "#1E1E1E",
                "primary": "#90CAF9",
                "secondary": "#B0B0B0",
                "text": "#FFFFFF",
                "text_secondary": "#B0B0B0",
                "border": "#2C2C2C",
                "error": "#EF5350",
                "success": "#66BB6A",
                "warning": "#FFA726"
            }
        }
    
    def get_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get theme data by name.
        
        Args:
            theme_name: Name of the theme.
        
        Returns:
            Theme data dictionary.
        """
        return self.themes.get(theme_name, self.themes.get("light", {}))
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme to apply.
        """
        if theme_name not in self.themes:
            logger.warning("Theme not found: %s, using light", theme_name)
            theme_name = "light"
        
        self.current_theme_name = theme_name
        theme = self.themes[theme_name]
        colors = theme.get("colors", {})
        
        # Build Qt stylesheet
        stylesheet = self._build_stylesheet(colors)
        
        # Apply to application
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            logger.info("Applied theme: %s", theme_name)
    
    def _build_stylesheet(self, colors: Dict[str, str]) -> str:
        """Build Qt stylesheet from theme colors.
        
        Args:
            colors: Color token dictionary.
        
        Returns:
            Qt stylesheet string.
        """
        bg = colors.get("background", "#FFFFFF")
        surface = colors.get("surface", "#F5F5F5")
        primary = colors.get("primary", "#2196F3")
        text = colors.get("text", "#212121")
        text_secondary = colors.get("text_secondary", "#757575")
        border = colors.get("border", "#E0E0E0")
        
        return f"""
            QMainWindow {{
                background-color: {bg};
                color: {text};
            }}
            
            QWidget {{
                background-color: {bg};
                color: {text};
            }}
            
            QMenuBar {{
                background-color: {surface};
                color: {text};
                border-bottom: 1px solid {border};
            }}
            
            QMenuBar::item {{
                padding: 4px 12px;
                background-color: transparent;
            }}
            
            QMenuBar::item:selected {{
                background-color: {primary};
                color: white;
            }}
            
            QMenu {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
            }}
            
            QMenu::item {{
                padding: 6px 24px;
            }}
            
            QMenu::item:selected {{
                background-color: {primary};
                color: white;
            }}
            
            QPushButton {{
                background-color: {primary};
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {primary};
                opacity: 0.9;
            }}
            
            QLabel {{
                color: {text};
            }}
            
            QCheckBox {{
                color: {text};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {border};
                border-radius: 3px;
                background-color: {bg};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {primary};
                border-color: {primary};
                image: url(none);
            }}
            
            QCheckBox::indicator:checked::after {{
                content: "✓";
                color: white;
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {primary};
            }}
            
            QTextEdit {{
                background-color: {bg};
                color: {text};
                border: 2px solid {border};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QTextEdit:focus {{
                border-color: {primary};
            }}
            
            QLineEdit {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 4px;
            }}
            
            QLineEdit:focus {{
                border-color: {primary};
            }}
            
            QSpinBox, QDoubleSpinBox {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 3px;
            }}
            
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {primary};
            }}
            
            QComboBox {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 4px;
            }}
            
            QComboBox:focus {{
                border-color: {primary};
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
                selection-background-color: {primary};
                selection-color: white;
            }}
        """
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.
        
        Returns:
            Name of the newly applied theme.
        """
        new_theme = "dark" if self.current_theme_name == "light" else "light"
        self.apply_theme(new_theme)
        return new_theme