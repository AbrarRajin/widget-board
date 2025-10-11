"""Grid controller for layout management and collision detection."""

import logging
from typing import List, Optional, Tuple
from core.models import Tile

logger = logging.getLogger(__name__)


class GridController:
    """Controller for 8×8 grid layout with collision detection."""
    
    GRID_ROWS = 8
    GRID_COLS = 8
    
    def __init__(self) -> None:
        """Initialize grid controller."""
        self.tiles: List[Tile] = []
    
    def set_tiles(self, tiles: List[Tile]) -> None:
        """Set the current tiles in the grid.
        
        Args:
            tiles: List of tiles to manage.
        """
        self.tiles = tiles
        logger.debug("Grid controller loaded %d tiles", len(tiles))
    
    def add_tile(self, tile: Tile) -> bool:
        """Add a tile to the grid if it doesn't cause collisions.
        
        Args:
            tile: Tile to add.
        
        Returns:
            True if tile was added successfully, False if collision occurred.
        """
        if self.check_collision(tile, exclude_tile=None):
            logger.warning("Cannot add tile - collision detected: %s", tile)
            return False
        
        self.tiles.append(tile)
        logger.info("Added tile: %s", tile)
        return True
    
    def remove_tile(self, tile: Tile) -> None:
        """Remove a tile from the grid.
        
        Args:
            tile: Tile to remove.
        """
        if tile in self.tiles:
            self.tiles.remove(tile)
            logger.info("Removed tile: %s", tile)
    
    def move_tile(self, tile: Tile, new_row: int, new_col: int) -> bool:
        """Move a tile to a new position with collision detection.
        
        Args:
            tile: Tile to move.
            new_row: Target row.
            new_col: Target column.
        
        Returns:
            True if move was successful, False if collision occurred.
        """
        # Store original position
        old_row, old_col = tile.row, tile.col
        
        # Snap to grid bounds
        new_row, new_col = self.snap_position(new_row, new_col, tile.width, tile.height)
        
        # Try the move
        tile.row = new_row
        tile.col = new_col
        
        # Check for collisions
        if self.check_collision(tile, exclude_tile=tile):
            # Revert on collision
            tile.row = old_row
            tile.col = old_col
            logger.debug("Move blocked by collision")
            return False
        
        logger.debug("Moved tile to (%d, %d)", new_row, new_col)
        return True
    
    def resize_tile(self, tile: Tile, new_width: int, new_height: int) -> bool:
        """Resize a tile with collision detection.
        
        Args:
            tile: Tile to resize.
            new_width: New width in cells.
            new_height: New height in cells.
        
        Returns:
            True if resize was successful, False if collision occurred.
        """
        # Store original size
        old_width, old_height = tile.width, tile.height
        
        # Clamp size to valid range
        new_width = max(1, min(new_width, self.GRID_COLS))
        new_height = max(1, min(new_height, self.GRID_ROWS))
        
        # Ensure tile stays within grid bounds
        if tile.col + new_width > self.GRID_COLS:
            new_width = self.GRID_COLS - tile.col
        if tile.row + new_height > self.GRID_ROWS:
            new_height = self.GRID_ROWS - tile.row
        
        # Try the resize
        tile.width = new_width
        tile.height = new_height
        
        # Check for collisions
        if self.check_collision(tile, exclude_tile=tile):
            # Revert on collision
            tile.width = old_width
            tile.height = old_height
            logger.debug("Resize blocked by collision")
            return False
        
        logger.debug("Resized tile to %dx%d", new_width, new_height)
        return True
    
    def check_collision(self, tile: Tile, exclude_tile: Optional[Tile] = None) -> bool:
        """Check if a tile collides with any existing tiles.
        
        Args:
            tile: Tile to check.
            exclude_tile: Tile to exclude from collision check (typically the tile being moved).
        
        Returns:
            True if collision detected, False otherwise.
        """
        for other in self.tiles:
            if other is exclude_tile or other is tile:
                continue
            
            if tile.overlaps_with(other):
                return True
        
        return False
    
    def resolve_collision(self, tile: Tile) -> Tuple[int, int]:
        """Find the nearest non-colliding position for a tile.
        
        Uses a deterministic first-fit algorithm by reading order (left-to-right, top-to-bottom).
        
        Args:
            tile: Tile to place.
        
        Returns:
            Tuple of (row, col) for the nearest valid position.
        """
        # Try original position first
        if not self.check_collision(tile, exclude_tile=tile):
            return (tile.row, tile.col)
        
        # Search grid in reading order
        for row in range(self.GRID_ROWS - tile.height + 1):
            for col in range(self.GRID_COLS - tile.width + 1):
                # Try this position
                original_row, original_col = tile.row, tile.col
                tile.row = row
                tile.col = col
                
                if not self.check_collision(tile, exclude_tile=tile):
                    logger.info("Resolved collision: moved to (%d, %d)", row, col)
                    return (row, col)
                
                # Restore original position for next iteration
                tile.row = original_row
                tile.col = original_col
        
        # No valid position found - return original
        logger.warning("Could not resolve collision for tile: %s", tile)
        return (tile.row, tile.col)
    
    def snap_position(self, row: int, col: int, width: int, height: int) -> Tuple[int, int]:
        """Snap a position to valid grid bounds.
        
        Args:
            row: Desired row.
            col: Desired column.
            width: Tile width.
            height: Tile height.
        
        Returns:
            Tuple of (snapped_row, snapped_col).
        """
        # Clamp to grid boundaries
        row = max(0, min(row, self.GRID_ROWS - height))
        col = max(0, min(col, self.GRID_COLS - width))
        
        return (row, col)
    
    def get_tile_at(self, row: int, col: int) -> Optional[Tile]:
        """Get the tile at a specific cell position.
        
        Args:
            row: Row index.
            col: Column index.
        
        Returns:
            Tile at the position, or None if empty.
        """
        for tile in self.tiles:
            if tile.contains_cell(row, col):
                return tile
        return None
    
    def find_empty_slot(self, width: int, height: int) -> Optional[Tuple[int, int]]:
        """Find an empty slot that can fit a tile of given size.
        
        Args:
            width: Required width.
            height: Required height.
        
        Returns:
            Tuple of (row, col) for first available slot, or None if grid is full.
        """
        for row in range(self.GRID_ROWS - height + 1):
            for col in range(self.GRID_COLS - width + 1):
                # Check if this area is free
                is_free = True
                for r in range(row, row + height):
                    for c in range(col, col + width):
                        if self.get_tile_at(r, c) is not None:
                            is_free = False
                            break
                    if not is_free:
                        break
                
                if is_free:
                    return (row, col)
        
        return None
    
    def get_grid_occupancy(self) -> List[List[Optional[Tile]]]:
        """Get a 2D grid showing which tile occupies each cell.
        
        Returns:
            8×8 grid where each cell contains the Tile occupying it, or None if empty.
        """
        grid = [[None for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
        
        for tile in self.tiles:
            for row in range(tile.row, tile.row + tile.height):
                for col in range(tile.col, tile.col + tile.width):
                    grid[row][col] = tile
        
        return grid
