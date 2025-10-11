"""Data models for pages and tiles."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json


@dataclass
class Page:
    """Represents a dashboard page."""
    
    id: int
    name: str
    index_order: int = 0
    
    def __repr__(self) -> str:
        return f"Page(id={self.id}, name='{self.name}', index={self.index_order})"


@dataclass
class Tile:
    """Represents a widget tile on a page."""
    
    id: Optional[int]
    page_id: int
    plugin_id: str
    instance_id: str
    row: int
    col: int
    width: int
    height: int
    z_index: int = 0
    state: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate tile properties."""
        if self.row < 0 or self.row >= 8:
            raise ValueError(f"Row must be 0-7, got {self.row}")
        if self.col < 0 or self.col >= 8:
            raise ValueError(f"Col must be 0-7, got {self.col}")
        if self.width < 1 or self.width > 8:
            raise ValueError(f"Width must be 1-8, got {self.width}")
        if self.height < 1 or self.height > 8:
            raise ValueError(f"Height must be 1-8, got {self.height}")
        if self.col + self.width > 8:
            raise ValueError(f"Tile extends beyond grid: col={self.col}, width={self.width}")
        if self.row + self.height > 8:
            raise ValueError(f"Tile extends beyond grid: row={self.row}, height={self.height}")
    
    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Get tile bounds as (row, col, row_end, col_end).
        
        Returns:
            Tuple of (row, col, row + height, col + width).
        """
        return (self.row, self.col, self.row + self.height, self.col + self.width)
    
    def overlaps_with(self, other: 'Tile') -> bool:
        """Check if this tile overlaps with another tile.
        
        Args:
            other: Another tile to check against.
        
        Returns:
            True if tiles overlap, False otherwise.
        """
        r1, c1, r2, c2 = self.bounds
        or1, oc1, or2, oc2 = other.bounds
        
        # Check if rectangles overlap
        return not (r2 <= or1 or r1 >= or2 or c2 <= oc1 or c1 >= oc2)
    
    def contains_cell(self, row: int, col: int) -> bool:
        """Check if tile contains a specific cell.
        
        Args:
            row: Row index.
            col: Column index.
        
        Returns:
            True if cell is within tile bounds.
        """
        return (self.row <= row < self.row + self.height and
                self.col <= col < self.col + self.width)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tile to dictionary for storage.
        
        Returns:
            Dictionary representation of tile.
        """
        return {
            'id': self.id,
            'page_id': self.page_id,
            'plugin_id': self.plugin_id,
            'instance_id': self.instance_id,
            'row': self.row,
            'col': self.col,
            'width': self.width,
            'height': self.height,
            'z_index': self.z_index,
            'state_json': json.dumps(self.state)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tile':
        """Create tile from dictionary.
        
        Args:
            data: Dictionary with tile data.
        
        Returns:
            New Tile instance.
        """
        state_json = data.get('state_json', '{}')
        state = json.loads(state_json) if state_json else {}
        
        return cls(
            id=data.get('id'),
            page_id=data['page_id'],
            plugin_id=data['plugin_id'],
            instance_id=data['instance_id'],
            row=data['row'],
            col=data['col'],
            width=data['width'],
            height=data['height'],
            z_index=data.get('z_index', 0),
            state=state
        )
    
    def __repr__(self) -> str:
        return (f"Tile(id={self.id}, plugin='{self.plugin_id}', "
                f"pos=({self.row},{self.col}), size=({self.width}×{self.height}))")
