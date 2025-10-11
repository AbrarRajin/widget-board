"""Tests for grid controller."""

import unittest
from core.models import Tile
from core.grid_controller import GridController


class TestGridController(unittest.TestCase):
    """Test cases for GridController."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = GridController()
    
    def test_add_tile_no_collision(self):
        """Test adding a tile without collision."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        
        result = self.controller.add_tile(tile)
        self.assertTrue(result)
        self.assertEqual(len(self.controller.tiles), 1)
    
    def test_add_tile_with_collision(self):
        """Test that adding a colliding tile fails."""
        tile1 = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        tile2 = Tile(
            id=2, page_id=1, plugin_id="test", instance_id="test-2",
            row=1, col=1, width=2, height=2
        )
        
        self.controller.add_tile(tile1)
        result = self.controller.add_tile(tile2)
        
        self.assertFalse(result)
        self.assertEqual(len(self.controller.tiles), 1)
    
    def test_move_tile_valid(self):
        """Test moving a tile to a valid position."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        self.controller.add_tile(tile)
        
        result = self.controller.move_tile(tile, 2, 2)
        
        self.assertTrue(result)
        self.assertEqual(tile.row, 2)
        self.assertEqual(tile.col, 2)
    
    def test_move_tile_collision(self):
        """Test that moving a tile into collision fails."""
        tile1 = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        tile2 = Tile(
            id=2, page_id=1, plugin_id="test", instance_id="test-2",
            row=4, col=4, width=2, height=2
        )
        
        self.controller.add_tile(tile1)
        self.controller.add_tile(tile2)
        
        # Try to move tile2 onto tile1
        result = self.controller.move_tile(tile2, 1, 1)
        
        self.assertFalse(result)
        self.assertEqual(tile2.row, 4)
        self.assertEqual(tile2.col, 4)
    
    def test_resize_tile_valid(self):
        """Test resizing a tile."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        self.controller.add_tile(tile)
        
        result = self.controller.resize_tile(tile, 3, 3)
        
        self.assertTrue(result)
        self.assertEqual(tile.width, 3)
        self.assertEqual(tile.height, 3)
    
    def test_resize_tile_collision(self):
        """Test that resizing into collision fails."""
        tile1 = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        tile2 = Tile(
            id=2, page_id=1, plugin_id="test", instance_id="test-2",
            row=0, col=3, width=2, height=2
        )
        
        self.controller.add_tile(tile1)
        self.controller.add_tile(tile2)
        
        # Try to resize tile1 to overlap tile2
        result = self.controller.resize_tile(tile1, 4, 2)
        
        self.assertFalse(result)
        self.assertEqual(tile1.width, 2)
    
    def test_snap_position(self):
        """Test position snapping to grid bounds."""
        # Normal position
        row, col = self.controller.snap_position(3, 3, 2, 2)
        self.assertEqual((row, col), (3, 3))
        
        # Out of bounds - should clamp
        row, col = self.controller.snap_position(7, 7, 2, 2)
        self.assertEqual((row, col), (6, 6))
        
        # Negative - should clamp to 0
        row, col = self.controller.snap_position(-1, -1, 2, 2)
        self.assertEqual((row, col), (0, 0))
    
    def test_get_tile_at(self):
        """Test getting tile at a specific position."""
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=2, col=3, width=2, height=2
        )
        self.controller.add_tile(tile)
        
        # Inside tile
        found = self.controller.get_tile_at(3, 4)
        self.assertEqual(found, tile)
        
        # Outside tile
        found = self.controller.get_tile_at(0, 0)
        self.assertIsNone(found)
    
    def test_find_empty_slot(self):
        """Test finding empty slots."""
        # Empty grid
        slot = self.controller.find_empty_slot(2, 2)
        self.assertEqual(slot, (0, 0))
        
        # With some tiles
        tile = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        self.controller.add_tile(tile)
        
        slot = self.controller.find_empty_slot(2, 2)
        self.assertIsNotNone(slot)
        self.assertNotEqual(slot, (0, 0))
    
    def test_resolve_collision(self):
        """Test collision resolution."""
        tile1 = Tile(
            id=1, page_id=1, plugin_id="test", instance_id="test-1",
            row=0, col=0, width=2, height=2
        )
        self.controller.add_tile(tile1)
        
        # Create colliding tile
        tile2 = Tile(
            id=2, page_id=1, plugin_id="test", instance_id="test-2",
            row=1, col=1, width=2, height=2
        )
        
        # Resolve collision
        new_row, new_col = self.controller.resolve_collision(tile2)
        
        # Should find a non-colliding position
        self.assertNotEqual((new_row, new_col), (1, 1))


if __name__ == "__main__":
    unittest.main()
