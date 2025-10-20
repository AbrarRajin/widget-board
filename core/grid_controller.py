"""Grid controller for layout management and collision detection."""

import logging
from typing import List, Optional, Tuple, Dict
from core.models import Tile, Page

logger = logging.getLogger(__name__)


class GridController:
    """Controller for 8×8 grid layout with collision detection and multi-page support."""
    
    GRID_ROWS = 8
    GRID_COLS = 8
    
    def __init__(self) -> None:
        """Initialize grid controller."""
        self.pages: List[Page] = []
        self.tiles_by_page: Dict[int, List[Tile]] = {}  # page_id -> tiles
        self.current_page: Optional[Page] = None
    
    @property
    def tiles(self) -> List[Tile]:
        """Get tiles for the current page.
        
        Returns:
            List of tiles on the current page.
        """
        if self.current_page:
            return self.tiles_by_page.get(self.current_page.id, [])
        return []
    
    def switch_to_page(self, page_id: int) -> bool:
        """Switch to a different page.
        
        Args:
            page_id: ID of the page to switch to.
            
        Returns:
            True if successful, False if page not found.
        """
        for page in self.pages:
            if page.id == page_id:
                self.current_page = page
                logger.info(f"Switched to page: {page.name}")
                return True
        
        logger.warning(f"Page not found: {page_id}")
        return False
    
    def find_empty_space(self, width: int, height: int) -> Optional[Tuple[int, int]]:
        """Find an empty space in the current page that can fit a tile.
        
        Args:
            width: Required width in grid cells.
            height: Required height in grid cells.
            
        Returns:
            Tuple of (row, col) for first available space, or None if no space.
        """
        tiles = self.tiles
        
        for row in range(self.GRID_ROWS - height + 1):
            for col in range(self.GRID_COLS - width + 1):
                # Check if this area is free
                is_free = True
                for r in range(row, row + height):
                    for c in range(col, col + width):
                        # Check if any tile occupies this cell
                        for tile in tiles:
                            if (tile.row <= r < tile.row + tile.height and
                                tile.col <= c < tile.col + tile.width):
                                is_free = False
                                break
                        if not is_free:
                            break
                    if not is_free:
                        break
                
                if is_free:
                    return (row, col)
        
        return None
    
    def add_tile(self, tile: Tile) -> bool:
        """Add a tile to the current page if it doesn't cause collisions.
        
        Args:
            tile: Tile to add.
        
        Returns:
            True if tile was added successfully, False if collision occurred.
        """
        if not self.current_page:
            logger.warning("No current page selected")
            return False
        
        # Ensure tile is for current page
        if tile.page_id != self.current_page.id:
            logger.warning(f"Tile page_id {tile.page_id} doesn't match current page {self.current_page.id}")
            return False
        
        # Check collision
        if self.check_collision(tile, exclude_id=None):
            logger.warning("Cannot add tile - collision detected")
            return False
        
        # Add to tiles list
        if self.current_page.id not in self.tiles_by_page:
            self.tiles_by_page[self.current_page.id] = []
        
        self.tiles_by_page[self.current_page.id].append(tile)
        logger.info(f"Added tile at ({tile.row}, {tile.col})")
        return True
    
    def remove_tile(self, tile_id: Optional[int]) -> bool:
        """Remove a tile from the current page.
        
        Args:
            tile_id: ID of the tile to remove.
        
        Returns:
            True if removed, False if not found.
        """
        if not self.current_page or tile_id is None:
            return False
        
        tiles = self.tiles_by_page.get(self.current_page.id, [])
        for i, tile in enumerate(tiles):
            if tile.id == tile_id:
                tiles.pop(i)
                logger.info(f"Removed tile {tile_id}")
                return True
        
        return False
    
    def move_tile(self, tile_id: Optional[int], new_row: int, new_col: int) -> bool:
        """Move a tile to a new position with collision detection.
        
        Args:
            tile_id: ID of the tile to move.
            new_row: Target row.
            new_col: Target column.
        
        Returns:
            True if move was successful, False if collision occurred.
        """
        if not self.current_page or tile_id is None:
            return False
        
        # Find the tile
        tile = None
        for t in self.tiles:
            if t.id == tile_id:
                tile = t
                break
        
        if not tile:
            return False
        
        # Check bounds
        if new_row < 0 or new_col < 0:
            return False
        if new_row + tile.height > self.GRID_ROWS:
            return False
        if new_col + tile.width > self.GRID_COLS:
            return False
        
        # Save old position
        old_row, old_col = tile.row, tile.col
        
        # Try new position
        tile.row = new_row
        tile.col = new_col
        
        # Check collision
        if self.check_collision(tile, exclude_id=tile_id):
            # Collision - revert
            tile.row = old_row
            tile.col = old_col
            return False
        
        logger.debug(f"Moved tile {tile_id} to ({new_row}, {new_col})")
        return True
    
    def resize_tile(self, tile_id: Optional[int], new_width: int, new_height: int) -> bool:
        """Resize a tile with collision detection.
        
        Args:
            tile_id: ID of the tile to resize.
            new_width: New width in grid cells.
            new_height: New height in grid cells.
        
        Returns:
            True if resize was successful, False if collision occurred.
        """
        if not self.current_page or tile_id is None:
            return False
        
        # Find the tile
        tile = None
        for t in self.tiles:
            if t.id == tile_id:
                tile = t
                break
        
        if not tile:
            return False
        
        # Validate size
        if new_width < 1 or new_height < 1:
            return False
        if new_width > self.GRID_COLS or new_height > self.GRID_ROWS:
            return False
        
        # Check bounds
        if tile.row + new_height > self.GRID_ROWS:
            return False
        if tile.col + new_width > self.GRID_COLS:
            return False
        
        # Save old size
        old_width, old_height = tile.width, tile.height
        
        # Try new size
        tile.width = new_width
        tile.height = new_height
        
        # Check collision
        if self.check_collision(tile, exclude_id=tile_id):
            # Collision - revert
            tile.width = old_width
            tile.height = old_height
            return False
        
        logger.debug(f"Resized tile {tile_id} to {new_width}×{new_height}")
        return True
    
    def check_collision(self, tile: Tile, exclude_id: Optional[int]) -> bool:
        """Check if a tile would collide with other tiles.
        
        Args:
            tile: Tile to check.
            exclude_id: ID of tile to exclude from collision check (usually the tile being moved).
        
        Returns:
            True if collision detected, False otherwise.
        """
        for other in self.tiles:
            # Skip self
            if other.id == exclude_id:
                continue
            
            # Check overlap
            if tile.overlaps_with(other):
                return True
        
        return False
    
    def snap_to_grid(self, row: int, col: int, width: int, height: int) -> Tuple[int, int]:
        """Snap a position to grid boundaries.
        
        Args:
            row: Proposed row.
            col: Proposed column.
            width: Tile width.
            height: Tile height.
        
        Returns:
            Tuple of (snapped_row, snapped_col).
        """
        row = max(0, min(row, self.GRID_ROWS - height))
        col = max(0, min(col, self.GRID_COLS - width))
        return (row, col)