"""SQLite repository for application data."""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from storage.migrations import apply_migrations, get_schema_version

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for managing SQLite database operations."""
    
    def __init__(self, db_path: Path) -> None:
        """Initialize repository with database path.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    def initialize(self) -> None:
        """Initialize the database and apply migrations."""
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        self._conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        self._conn.execute("PRAGMA foreign_keys = ON")
        
        # Apply migrations
        apply_migrations(self._conn)
        
        version = get_schema_version(self._conn)
        logger.info("Database initialized at version %d", version)
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions.
        
        Yields:
            Database cursor for executing queries.
        """
        if not self._conn:
            raise RuntimeError("Database not initialized")
        
        cursor = self._conn.cursor()
        try:
            cursor.execute("BEGIN")
            yield cursor
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cursor.close()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor.
        
        Args:
            query: SQL query string.
            params: Query parameters.
        
        Returns:
            Cursor with query results.
        """
        if not self._conn:
            raise RuntimeError("Database not initialized")
        
        return self._conn.execute(query, params)
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")
    
    # App Settings Methods
    
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get an application setting value.
        
        Args:
            key: Setting key.
            default: Default value if key not found.
        
        Returns:
            Setting value or default.
        """
        cursor = self.execute(
            "SELECT value_json FROM app_settings WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            return json.loads(row["value_json"])
        return default
    
    def set_app_setting(self, key: str, value: Any) -> None:
        """Set an application setting value.
        
        Args:
            key: Setting key.
            value: Setting value (must be JSON-serializable).
        """
        value_json = json.dumps(value)
        self.execute(
            """
            INSERT INTO app_settings (key, value_json)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json = excluded.value_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value_json)
        )
    
    # Page Methods
    
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """Get all pages ordered by index.
        
        Returns:
            List of page dictionaries.
        """
        cursor = self.execute(
            "SELECT id, name, index_order FROM pages ORDER BY index_order"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def create_page(self, name: str, index_order: int = 0) -> int:
        """Create a new page.
        
        Args:
            name: Page name.
            index_order: Display order.
        
        Returns:
            New page ID.
        """
        cursor = self.execute(
            "INSERT INTO pages (name, index_order) VALUES (?, ?)",
            (name, index_order)
        )
        return cursor.lastrowid
    
    def delete_page(self, page_id: int) -> None:
        """Delete a page and all its tiles.
        
        Args:
            page_id: Page ID to delete.
        """
        self.execute("DELETE FROM pages WHERE id = ?", (page_id,))
    
    # Tile Methods
    
    def get_tiles_for_page(self, page_id: int) -> List[Dict[str, Any]]:
        """Get all tiles for a given page.
        
        Args:
            page_id: Page ID.
        
        Returns:
            List of tile dictionaries.
        """
        cursor = self.execute(
            """
            SELECT id, page_id, plugin_id, instance_id,
                   row, col, width, height, z_index, state_json
            FROM tiles
            WHERE page_id = ?
            ORDER BY z_index, row, col
            """,
            (page_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def create_tile(self, tile_data: Dict[str, Any]) -> int:
        """Create a new tile.
        
        Args:
            tile_data: Tile data dictionary.
        
        Returns:
            New tile ID.
        """
        cursor = self.execute(
            """
            INSERT INTO tiles (page_id, plugin_id, instance_id, row, col, 
                               width, height, z_index, state_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tile_data['page_id'],
                tile_data['plugin_id'],
                tile_data['instance_id'],
                tile_data['row'],
                tile_data['col'],
                tile_data['width'],
                tile_data['height'],
                tile_data.get('z_index', 0),
                tile_data.get('state_json', '{}')
            )
        )
        return cursor.lastrowid
    
    def update_tile(self, tile_id: int, tile_data: Dict[str, Any]) -> None:
        """Update an existing tile.
        
        Args:
            tile_id: Tile ID to update.
            tile_data: Updated tile data.
        """
        self.execute(
            """
            UPDATE tiles
            SET row = ?, col = ?, width = ?, height = ?, 
                z_index = ?, state_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                tile_data['row'],
                tile_data['col'],
                tile_data['width'],
                tile_data['height'],
                tile_data.get('z_index', 0),
                tile_data.get('state_json', '{}'),
                tile_id
            )
        )
    
    def delete_tile(self, tile_id: int) -> None:
        """Delete a tile.
        
        Args:
            tile_id: Tile ID to delete.
        """
        self.execute("DELETE FROM tiles WHERE id = ?", (tile_id,))
    
    def save_tiles_for_page(self, page_id: int, tiles: List[Dict[str, Any]]) -> None:
        """Replace all tiles for a page with a new set.
        
        Args:
            page_id: Page ID.
            tiles: List of tile dictionaries.
        """
        with self.transaction():
            # Delete existing tiles
            self.execute("DELETE FROM tiles WHERE page_id = ?", (page_id,))
            
            # Insert new tiles
            for tile in tiles:
                self.create_tile(tile)
