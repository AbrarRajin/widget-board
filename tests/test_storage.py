"""Tests for storage repository."""

import unittest
import tempfile
from pathlib import Path
from storage.repository import StorageRepository
from storage.migrations import CURRENT_SCHEMA_VERSION, get_schema_version


class TestStorageRepository(unittest.TestCase):
    """Test cases for StorageRepository."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.repo = StorageRepository(self.db_path)
        self.repo.initialize()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.repo.close()
    
    def test_database_initialization(self):
        """Test that database is initialized with correct schema."""
        self.assertTrue(self.db_path.exists())
        
        # Check schema version
        version = get_schema_version(self.repo._conn)
        self.assertEqual(version, CURRENT_SCHEMA_VERSION)
    
    def test_app_settings(self):
        """Test application settings storage and retrieval."""
        # Set a setting
        self.repo.set_app_setting("test_key", {"value": 123})
        
        # Retrieve it
        result = self.repo.get_app_setting("test_key")
        self.assertEqual(result, {"value": 123})
        
        # Test default value for missing key
        result = self.repo.get_app_setting("missing", "default")
        self.assertEqual(result, "default")
    
    def test_page_creation(self):
        """Test page creation and retrieval."""
        # Create a page
        page_id = self.repo.create_page("Test Page", index_order=0)
        self.assertIsNotNone(page_id)
        
        # Retrieve all pages
        pages = self.repo.get_all_pages()
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["name"], "Test Page")
    
    def test_page_deletion(self):
        """Test page deletion."""
        # Create and delete a page
        page_id = self.repo.create_page("Temp Page")
        self.repo.delete_page(page_id)
        
        # Verify it's gone
        pages = self.repo.get_all_pages()
        self.assertEqual(len(pages), 0)
    
    def test_transaction_rollback(self):
        """Test that transaction rollback works."""
        try:
            with self.repo.transaction() as cursor:
                cursor.execute("INSERT INTO pages (name) VALUES (?)", ("Test",))
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify rollback occurred
        pages = self.repo.get_all_pages()
        self.assertEqual(len(pages), 0)


if __name__ == "__main__":
    unittest.main()
