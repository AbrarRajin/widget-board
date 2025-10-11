"""Tests for configuration management."""

import unittest
import tempfile
import json
from pathlib import Path
from core.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
    
    def test_default_values(self):
        """Test that default configuration values are set."""
        self.assertEqual(self.config.app_name, "WidgetBoard")
        self.assertEqual(self.config.version, "0.1.0")
        self.assertEqual(self.config.theme, "light")
        self.assertEqual(self.config.grid_rows, 8)
        self.assertEqual(self.config.grid_cols, 8)
    
    def test_platform_paths_exist(self):
        """Test that platform-aware paths are created."""
        self.assertTrue(self.config.config_dir.exists())
        self.assertTrue(self.config.data_dir.exists())
        self.assertTrue(self.config.log_dir.exists())
    
    def test_get_method(self):
        """Test configuration value retrieval."""
        self.assertEqual(self.config.get("theme"), "light")
        self.assertEqual(self.config.get("nonexistent", "default"), "default")
    
    def test_save_and_load_settings(self):
        """Test settings persistence."""
        # Create temporary settings file
        temp_settings = Path(self.temp_dir) / "test_settings.json"
        self.config.settings_file = temp_settings
        
        # Modify and save
        self.config.theme = "dark"
        self.config.window_width = 1920
        self.config.save_settings()
        
        # Verify file was created
        self.assertTrue(temp_settings.exists())
        
        # Load and verify
        with open(temp_settings, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["theme"], "dark")
        self.assertEqual(data["window_width"], 1920)


if __name__ == "__main__":
    unittest.main()
