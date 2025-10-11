"""Tests for data models."""

import unittest
from core.models import Tile, Page


class TestTile(unittest.TestCase):
    """Test cases for Tile model."""
    
    def test_valid_tile(self):
        """Test creating a valid tile."""
        tile = Tile(
            id=1,
            page_id=1,
            plugin_id="test",
            instance_id="test-1",
            row=0,
            col=0,
            width=2,
            height=2
        )
        
        self.assertEqual(tile.row, 0)
        self.assertEqual(tile.col, 0)
        self.assertEqual(tile.width, 2)
        self.assertEqual(tile.height, 2)
    
    def test_invalid_row(self):
        """Test that invalid row raises error."""
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=-1, col=0, width=2, height=2
            )
        
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=8, col=0, width=2, height=2
            )
    
    def test_invalid_col(self):
        """Test that invalid column raises error."""
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=0, col=-1, width=2, height=2
            )
        
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=0, col=8, width=2, height=2
            )
    
    def test_invalid_size(self):
        """Test that invalid size raises error."""
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=0, col=0, width=0, height=2
            )
        
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=0, col=0, width=2, height=9
            )
    
    def test_out_of_bounds(self):
        """Test that tile extending beyond grid raises error."""
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=0, col=7, width=2, height=2
            )
        
        with self.assertRaises(ValueError):
            Tile(
                id=1, page_id=1, plugin_id="test", instance_id="test-1",
                row=7, col=0, width=2, height=2
            )
    
    def test_bounds_property(self):
        """Test bounds calculation."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=2, col=3, width=2, height=3
        )
        
        bounds = tile.bounds
        self.assertEqual(bounds, (2, 3, 5, 5))
    
    def test_overlaps_with(self):
        """Test overlap detection."""
        tile1 = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        
        # Overlapping tile
        tile2 = Tile(
            id=2, page_id=1, plugin_id="test", instance_id="test-2",
            row=1, col=1, width=2, height=2
        )
        self.assertTrue(tile1.overlaps_with(tile2))
        
        # Non-overlapping tile
        tile3 = Tile(
            id=3, page_id=1, plugin_id="test", instance_id="test-3",
            row=3, col=3, width=2, height=2
        )
        self.assertFalse(tile1.overlaps_with(tile3))
        
        # Adjacent but not overlapping
        tile4 = Tile(
            id=4, page_id=1, plugin_id="test", instance_id="test-4",
            row=0, col=2, width=2, height=2
        )
        self.assertFalse(tile1.overlaps_with(tile4))
    
    def test_contains_cell(self):
        """Test cell containment check."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=2, col=3, width=2, height=2
        )
        
        # Inside
        self.assertTrue(tile.contains_cell(2, 3))
        self.assertTrue(tile.contains_cell(3, 4))
        
        # Outside
        self.assertFalse(tile.contains_cell(0, 0))
        self.assertFalse(tile.contains_cell(4, 5))
        
        # On boundary (exclusive)
        self.assertFalse(tile.contains_cell(4, 3))
        self.assertFalse(tile.contains_cell(2, 5))
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        tile = Tile(
            id=1,
            page_id=1,
            plugin_id="test",
            instance_id="test-1",
            row=2,
            col=3,
            width=2,
            height=3,
            z_index=5,
            state={"key": "value"}
        )
        
        # Serialize
        data = tile.to_dict()
        
        # Deserialize
        tile2 = Tile.from_dict(data)
        
        self.assertEqual(tile.id, tile2.id)
        self.assertEqual(tile.row, tile2.row)
        self.assertEqual(tile.col, tile2.col)
        self.assertEqual(tile.width, tile2.width)
        self.assertEqual(tile.height, tile2.height)
        self.assertEqual(tile.z_index, tile2.z_index)
        self.assertEqual(tile.state, tile2.state)


class TestPage(unittest.TestCase):
    """Test cases for Page model."""
    
    def test_create_page(self):
        """Test creating a page."""
        page = Page(id=1, name="Test Page", index_order=0)
        
        self.assertEqual(page.id, 1)
        self.assertEqual(page.name, "Test Page")
        self.assertEqual(page.index_order, 0)


if __name__ == "__main__":
    unittest.main()
