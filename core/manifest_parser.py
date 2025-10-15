"""Plugin manifest parser.

Parses manifest.json files from plugin directories.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from core.plugin_api import PluginMetadata


logger = logging.getLogger(__name__)


class ManifestParser:
    """Parser for plugin manifest files."""
    
    REQUIRED_FIELDS = [
        "plugin_id",
        "name",
        "version",
        "description",
        "author",
        "module_path",
        "class_name"
    ]
    
    @staticmethod
    def parse(manifest_path: Path) -> Optional[PluginMetadata]:
        """Parse a manifest.json file.
        
        Args:
            manifest_path: Path to the manifest.json file.
            
        Returns:
            PluginMetadata if successful, None if parsing failed.
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            for field in ManifestParser.REQUIRED_FIELDS:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in {manifest_path}")
                    return None
            
            # Get plugin directory for resolving relative paths
            plugin_dir = manifest_path.parent
            
            # Parse schema path (relative to plugin directory)
            schema_path = None
            if "schema_path" in data:
                schema_file = plugin_dir / data["schema_path"]
                if schema_file.exists():
                    schema_path = str(schema_file)
                else:
                    logger.warning(f"Schema file not found: {schema_file}")
            
            # Parse icon path (relative to plugin directory)
            icon_path = None
            if "icon_path" in data:
                icon_file = plugin_dir / data["icon_path"]
                if icon_file.exists():
                    icon_path = str(icon_file)
                else:
                    logger.warning(f"Icon file not found: {icon_file}")
            
            # Parse size constraints
            constraints = data.get("size_constraints", {})
            
            metadata = PluginMetadata(
                plugin_id=data["plugin_id"],
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data["author"],
                module_path=data["module_path"],
                class_name=data["class_name"],
                schema_path=schema_path,
                icon_path=icon_path,
                min_width=constraints.get("min_width", 1),
                min_height=constraints.get("min_height", 1),
                max_width=constraints.get("max_width", 8),
                max_height=constraints.get("max_height", 8),
                default_width=constraints.get("default_width", 2),
                default_height=constraints.get("default_height", 2)
            )
            
            logger.info(f"Loaded plugin manifest: {metadata.name} v{metadata.version}")
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {manifest_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing manifest {manifest_path}: {e}")
            return None
