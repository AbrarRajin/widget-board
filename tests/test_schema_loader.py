"""Tests for schema loader."""

import unittest
import tempfile
import json
from pathlib import Path
from core.schema_loader import SchemaLoader


class TestSchemaLoader(unittest.TestCase):
    """Test cases for SchemaLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.schema_loader = SchemaLoader(Path(self.temp_dir))
        
        # Create a test schema
        self.test_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Test Schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "default": "Test"
                },
                "count": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 10
                },
                "enabled": {
                    "type": "boolean",
                    "default": True
                }
            },
            "required": ["name"]
        }
        
        # Write test schema to file
        schema_path = Path(self.temp_dir) / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(self.test_schema, f)
    
    def test_load_schema(self):
        """Test loading a schema from file."""
        schema_path = Path(self.temp_dir) / "test_schema.json"
        schema = self.schema_loader.load_schema(schema_path)
        
        self.assertEqual(schema["title"], "Test Schema")
        self.assertIn("properties", schema)
    
    def test_load_schema_by_name(self):
        """Test loading a schema by name."""
        schema = self.schema_loader.load_schema_by_name("test_schema")
        self.assertEqual(schema["title"], "Test Schema")
    
    def test_load_nonexistent_schema(self):
        """Test that loading nonexistent schema raises error."""
        with self.assertRaises(FileNotFoundError):
            self.schema_loader.load_schema(Path(self.temp_dir) / "missing.json")
    
    def test_validate_valid_data(self):
        """Test validating valid data against schema."""
        data = {
            "name": "Test Widget",
            "count": 42,
            "enabled": False
        }
        
        is_valid, error_msg = self.schema_loader.validate_data(data, self.test_schema)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_invalid_data(self):
        """Test validating invalid data against schema."""
        # Missing required field
        data = {
            "count": 42,
            "enabled": False
        }
        
        is_valid, error_msg = self.schema_loader.validate_data(data, self.test_schema)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
    
    def test_validate_wrong_type(self):
        """Test validation fails for wrong types."""
        data = {
            "name": "Test",
            "count": "not a number",  # Should be integer
            "enabled": True
        }
        
        is_valid, error_msg = self.schema_loader.validate_data(data, self.test_schema)
        self.assertFalse(is_valid)
    
    def test_get_default_values(self):
        """Test extracting default values from schema."""
        defaults = self.schema_loader.get_default_values(self.test_schema)
        
        self.assertEqual(defaults["name"], "Test")
        self.assertEqual(defaults["count"], 10)
        self.assertEqual(defaults["enabled"], True)
    
    def test_get_schema_metadata(self):
        """Test extracting schema metadata."""
        metadata = self.schema_loader.get_schema_metadata(self.test_schema)
        
        self.assertEqual(metadata["title"], "Test Schema")
        self.assertIn("name", metadata["properties"])
        self.assertIn("name", metadata["required"])


if __name__ == "__main__":
    unittest.main()