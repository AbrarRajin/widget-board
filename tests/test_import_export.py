"""Tests for import/export functionality."""

import unittest
import tempfile
import json
from pathlib import Path
from storage.repository import StorageRepository
from storage.import_export import LayoutImportExport
from core.models import Tile


class TestImportExport(unittest.TestCase):
    """Test cases for LayoutImportExport."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.export_path = Path(self.temp_dir) / "export.json"
        
        # Create repository
        self.repo = StorageRepository(self.db_path)
        self.repo.initialize()
        
        # Create importer/exporter
        self.import_export = LayoutImportExport(self.repo)
        
        # Create test data
        self.page_id = self.repo.create_page("Test Page", 0)
        
        tile = Tile(
            id=None,
            page_id=self.page_id,
            plugin_id="test_widget",
            instance_id="test-1",
            row=0,
            col=0,
            width=2,
            height=2,
            z_index=0,
            state={"test": "data"}
        )
        self.repo.create_tile(tile.to_dict())
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.repo.close()
    
    def test_export_layout(self):
        """Test exporting layout to JSON."""
        self.import_export.export_layout(self.export_path)
        
        # Verify file was created
        self.assertTrue(self.export_path.exists())
        
        # Load and verify content
        with open(self.export_path, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["version"], "1.0")
        self.assertIn("pages", data)
        self.assertEqual(len(data["pages"]), 1)
        
        page = data["pages"][0]
        self.assertEqual(page["name"], "Test Page")
        self.assertEqual(len(page["tiles"]), 1)
        
        tile = page["tiles"][0]
        self.assertEqual(tile["plugin_id"], "test_widget")
        self.assertEqual(tile["row"], 0)
        self.assertEqual(tile["col"], 0)
    
    def test_import_layout(self):
        """Test importing layout from JSON."""
        # First export
        self.import_export.export_layout(self.export_path)
        
        # Clear database
        self.repo.delete_page(self.page_id)
        
        # Import back
        pages_count, tiles_count = self.import_export.import_layout(self.export_path)
        
        self.assertEqual(pages_count, 1)
        self.assertEqual(tiles_count, 1)
        
        # Verify data
        pages = self.repo.get_all_pages()
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["name"], "Test Page")
    
    def test_import_merge(self):
        """Test merging imported layout with existing."""
        # Export current layout
        self.import_export.export_layout(self.export_path)
        
        # Create another page
        page2_id = self.repo.create_page("Page 2", 1)
        
        # Import with merge=True
        pages_count, tiles_count = self.import_export.import_layout(
            self.export_path,
            merge=True
        )
        
        # Should now have 3 pages (original + new + imported)
        pages = self.repo.get_all_pages()
        self.assertEqual(len(pages), 3)
    
    def test_validate_valid_layout(self):
        """Test validating a valid layout file."""
        self.import_export.export_layout(self.export_path)
        
        is_valid, message = self.import_export.validate_layout(self.export_path)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Layout file is valid")
    
    def test_validate_invalid_layout(self):
        """Test validating an invalid layout file."""
        # Create invalid JSON
        with open(self.export_path, "w") as f:
            json.dump({"invalid": "data"}, f)
        
        is_valid, message = self.import_export.validate_layout(self.export_path)
        self.assertFalse(is_valid)
        self.assertIn("version", message.lower())
    
    def test_validate_malformed_json(self):
        """Test validating malformed JSON."""
        with open(self.export_path, "w") as f:
            f.write("{ invalid json")
        
        is_valid, message = self.import_export.validate_layout(self.export_path)
        self.assertFalse(is_valid)
        self.assertIn("json", message.lower())
    
    def test_validate_tile_out_of_bounds(self):
        """Test validation catches tiles outside grid bounds."""
        layout_data = {
            "version": "1.0",
            "pages": [{
                "name": "Test",
                "tiles": [{
                    "plugin_id": "test",
                    "instance_id": "test-1",
                    "row": 10,  # Out of bounds
                    "col": 0,
                    "width": 2,
                    "height": 2
                }]
            }]
        }
        
        with open(self.export_path, "w") as f:
            json.dump(layout_data, f)
        
        is_valid, message = self.import_export.validate_layout(self.export_path)
        self.assertFalse(is_valid)
        self.assertIn("row", message.lower())


if __name__ == "__main__":
    unittest.main()