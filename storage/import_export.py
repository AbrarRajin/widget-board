"""Import and export layouts to/from JSON files."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from core.models import Page, Tile
from storage.repository import StorageRepository

logger = logging.getLogger(__name__)


class LayoutImportExport:
    """Handles import/export of dashboard layouts."""
    
    VERSION = "1.0"
    
    def __init__(self, repository: StorageRepository) -> None:
        """Initialize importer/exporter.
        
        Args:
            repository: Storage repository.
        """
        self.repository = repository
    
    def export_layout(self, output_path: Path, include_settings: bool = True) -> None:
        """Export current layout to JSON file.
        
        Args:
            output_path: Path to output JSON file.
            include_settings: Whether to include widget settings.
        
        Raises:
            OSError: If file cannot be written.
        """
        # Get all pages
        pages_data = self.repository.get_all_pages()
        pages = [Page(**p) for p in pages_data]
        
        # Build export data
        export_data = {
            "version": self.VERSION,
            "exported_at": datetime.now().isoformat(),
            "pages": []
        }
        
        for page in pages:
            page_data = {
                "name": page.name,
                "index_order": page.index_order,
                "tiles": []
            }
            
            # Get tiles for this page
            tiles_data = self.repository.get_tiles_for_page(page.id)
            
            for tile_dict in tiles_data:
                tile = Tile.from_dict(tile_dict)
                
                tile_export = {
                    "plugin_id": tile.plugin_id,
                    "instance_id": tile.instance_id,
                    "row": tile.row,
                    "col": tile.col,
                    "width": tile.width,
                    "height": tile.height,
                    "z_index": tile.z_index,
                    "state": tile.state
                }
                
                # Include settings if requested
                if include_settings:
                    settings = self.repository.get_app_setting(
                        f"widget_settings_{tile.instance_id}",
                        {}
                    )
                    tile_export["settings"] = settings
                
                page_data["tiles"].append(tile_export)
            
            export_data["pages"].append(page_data)
        
        # Also export app settings
        if include_settings:
            export_data["app_settings"] = {
                "theme": self.repository.get_app_setting("theme", "light")
            }
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
        
        logger.info("Exported layout to: %s", output_path)
    
    def import_layout(
        self, 
        input_path: Path, 
        merge: bool = False,
        import_settings: bool = True
    ) -> tuple[int, int]:
        """Import layout from JSON file.
        
        Args:
            input_path: Path to input JSON file.
            merge: If True, merge with existing layout. If False, replace.
            import_settings: Whether to import widget settings.
        
        Returns:
            Tuple of (pages_imported, tiles_imported).
        
        Raises:
            FileNotFoundError: If input file doesn't exist.
            json.JSONDecodeError: If JSON is invalid.
            ValueError: If layout data is invalid.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Import file not found: {input_path}")
        
        # Load JSON
        with open(input_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)
        
        # Validate version
        version = import_data.get("version")
        if version != self.VERSION:
            logger.warning("Import file version mismatch: %s (expected %s)", version, self.VERSION)
        
        pages_imported = 0
        tiles_imported = 0
        
        # Clear existing layout if not merging
        if not merge:
            existing_pages = self.repository.get_all_pages()
            for page_dict in existing_pages:
                self.repository.delete_page(page_dict['id'])
            logger.info("Cleared existing layout")
        
        # Import pages and tiles
        pages_data = import_data.get("pages", [])
        
        for page_data in pages_data:
            # Create page
            page_id = self.repository.create_page(
                page_data["name"],
                page_data.get("index_order", 0)
            )
            pages_imported += 1
            
            # Import tiles
            tiles_data = page_data.get("tiles", [])
            
            for tile_data in tiles_data:
                tile = Tile(
                    id=None,
                    page_id=page_id,
                    plugin_id=tile_data["plugin_id"],
                    instance_id=tile_data["instance_id"],
                    row=tile_data["row"],
                    col=tile_data["col"],
                    width=tile_data["width"],
                    height=tile_data["height"],
                    z_index=tile_data.get("z_index", 0),
                    state=tile_data.get("state", {})
                )
                
                # Save tile
                self.repository.create_tile(tile.to_dict())
                tiles_imported += 1
                
                # Import settings if present
                if import_settings and "settings" in tile_data:
                    self.repository.set_app_setting(
                        f"widget_settings_{tile.instance_id}",
                        tile_data["settings"]
                    )
        
        # Import app settings
        if import_settings and "app_settings" in import_data:
            app_settings = import_data["app_settings"]
            for key, value in app_settings.items():
                self.repository.set_app_setting(key, value)
        
        logger.info(
            "Imported %d pages, %d tiles from: %s",
            pages_imported, tiles_imported, input_path
        )
        
        return (pages_imported, tiles_imported)
    
    def validate_layout(self, input_path: Path) -> tuple[bool, str]:
        """Validate a layout JSON file without importing.
        
        Args:
            input_path: Path to input JSON file.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check required fields
            if "version" not in data:
                return (False, "Missing 'version' field")
            
            if "pages" not in data:
                return (False, "Missing 'pages' field")
            
            # Validate pages
            for i, page in enumerate(data["pages"]):
                if "name" not in page:
                    return (False, f"Page {i}: missing 'name'")
                
                if "tiles" not in page:
                    return (False, f"Page {i}: missing 'tiles'")
                
                # Validate tiles
                for j, tile in enumerate(page["tiles"]):
                    required = ["plugin_id", "instance_id", "row", "col", "width", "height"]
                    for field in required:
                        if field not in tile:
                            return (False, f"Page {i}, Tile {j}: missing '{field}'")
                    
                    # Validate bounds
                    try:
                        row, col = tile["row"], tile["col"]
                        width, height = tile["width"], tile["height"]
                        
                        if row < 0 or row >= 8:
                            return (False, f"Page {i}, Tile {j}: invalid row {row}")
                        if col < 0 or col >= 8:
                            return (False, f"Page {i}, Tile {j}: invalid col {col}")
                        if width < 1 or width > 8:
                            return (False, f"Page {i}, Tile {j}: invalid width {width}")
                        if height < 1 or height > 8:
                            return (False, f"Page {i}, Tile {j}: invalid height {height}")
                        if col + width > 8:
                            return (False, f"Page {i}, Tile {j}: extends beyond grid")
                        if row + height > 8:
                            return (False, f"Page {i}, Tile {j}: extends beyond grid")
                    
                    except (ValueError, TypeError) as e:
                        return (False, f"Page {i}, Tile {j}: invalid position/size - {e}")
            
            return (True, "Layout file is valid")
        
        except json.JSONDecodeError as e:
            return (False, f"Invalid JSON: {e}")
        except Exception as e:
            return (False, f"Validation error: {e}")