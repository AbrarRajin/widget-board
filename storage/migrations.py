"""Database schema migrations and versioning."""

import sqlite3
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


# Schema version history
CURRENT_SCHEMA_VERSION = 1

# Migration scripts: (version, description, sql)
MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        "Initial schema",
        """
        -- Schema version tracking
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );
        
        -- Pages in the dashboard
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            index_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name)
        );
        
        -- Tiles/widgets on pages
        CREATE TABLE IF NOT EXISTS tiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            plugin_id TEXT NOT NULL,
            instance_id TEXT NOT NULL UNIQUE,
            row INTEGER NOT NULL CHECK(row >= 0 AND row < 8),
            col INTEGER NOT NULL CHECK(col >= 0 AND col < 8),
            width INTEGER NOT NULL DEFAULT 1 CHECK(width > 0 AND width <= 8),
            height INTEGER NOT NULL DEFAULT 1 CHECK(height > 0 AND height <= 8),
            z_index INTEGER NOT NULL DEFAULT 0,
            state_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
            CHECK(col + width <= 8),
            CHECK(row + height <= 8)
        );
        
        -- Per-instance widget settings
        CREATE TABLE IF NOT EXISTS widget_settings (
            instance_id TEXT PRIMARY KEY,
            settings_json TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instance_id) REFERENCES tiles(instance_id) ON DELETE CASCADE
        );
        
        -- Global application settings
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Plugin performance telemetry
        CREATE TABLE IF NOT EXISTS telemetry (
            instance_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL,
            rss_mb REAL,
            last_update_ms INTEGER,
            missed_heartbeats INTEGER DEFAULT 0,
            FOREIGN KEY (instance_id) REFERENCES tiles(instance_id) ON DELETE CASCADE
        );
        
        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_tiles_page ON tiles(page_id);
        CREATE INDEX IF NOT EXISTS idx_tiles_position ON tiles(page_id, row, col);
        CREATE INDEX IF NOT EXISTS idx_telemetry_instance ON telemetry(instance_id, timestamp);
        """
    ),
]


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations to the database.
    
    Args:
        conn: SQLite connection.
    """
    cursor = conn.cursor()
    
    # Create schema version table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)
    
    # Get current version
    cursor.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version")
    current_version = cursor.fetchone()[0]
    
    logger.info("Current schema version: %d", current_version)
    
    # Apply pending migrations
    for version, description, sql in MIGRATIONS:
        if version > current_version:
            logger.info("Applying migration %d: %s", version, description)
            
            try:
                # Execute migration SQL
                cursor.executescript(sql)
                
                # Record migration
                cursor.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (version, description)
                )
                
                conn.commit()
                logger.info("Migration %d applied successfully", version)
            
            except sqlite3.Error as e:
                conn.rollback()
                logger.error("Migration %d failed: %s", version, e)
                raise
    
    if current_version == CURRENT_SCHEMA_VERSION:
        logger.info("Database schema is up to date")
    else:
        logger.info("Migrated from version %d to %d", current_version, CURRENT_SCHEMA_VERSION)


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get the current schema version.
    
    Args:
        conn: SQLite connection.
    
    Returns:
        Current schema version number.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version")
        return cursor.fetchone()[0]
    except sqlite3.Error:
        return 0
