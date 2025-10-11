"""JSON Schema loader and validator."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger(__name__)


class SchemaLoader:
    """Loads and validates JSON schemas for widget settings."""
    
    def __init__(self, schema_dir: Optional[Path] = None) -> None:
        """Initialize schema loader.
        
        Args:
            schema_dir: Directory containing schema files. Defaults to 'schema/'.
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "schema"
        
        self.schema_dir = schema_dir
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load a JSON schema from file.
        
        Args:
            schema_path: Path to schema file.
        
        Returns:
            Parsed schema dictionary.
        
        Raises:
            FileNotFoundError: If schema file doesn't exist.
            json.JSONDecodeError: If schema is invalid JSON.
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        # Check cache
        cache_key = str(schema_path)
        if cache_key in self.schema_cache:
            return self.schema_cache[cache_key]
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # Validate the schema itself
        Draft7Validator.check_schema(schema)
        
        # Cache it
        self.schema_cache[cache_key] = schema
        logger.info("Loaded schema: %s", schema_path.name)
        
        return schema
    
    def load_schema_by_name(self, name: str) -> Dict[str, Any]:
        """Load a schema by filename.
        
        Args:
            name: Schema filename (with or without .json extension).
        
        Returns:
            Parsed schema dictionary.
        """
        if not name.endswith('.json'):
            name = f"{name}.json"
        
        schema_path = self.schema_dir / name
        return self.load_schema(schema_path)
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate data against a schema.
        
        Args:
            data: Data to validate.
            schema: JSON schema.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            validate(instance=data, schema=schema)
            return (True, None)
        except ValidationError as e:
            error_msg = f"Validation error at {'.'.join(str(p) for p in e.path)}: {e.message}"
            logger.warning("Schema validation failed: %s", error_msg)
            return (False, error_msg)
    
    def get_default_values(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract default values from a schema.
        
        Args:
            schema: JSON schema.
        
        Returns:
            Dictionary of default values.
        """
        defaults = {}
        
        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if "default" in prop_schema:
                defaults[key] = prop_schema["default"]
            elif prop_schema.get("type") == "string":
                defaults[key] = ""
            elif prop_schema.get("type") == "number":
                defaults[key] = 0
            elif prop_schema.get("type") == "integer":
                defaults[key] = 0
            elif prop_schema.get("type") == "boolean":
                defaults[key] = False
            elif prop_schema.get("type") == "array":
                defaults[key] = []
            elif prop_schema.get("type") == "object":
                defaults[key] = {}
        
        return defaults
    
    def get_schema_metadata(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from schema.
        
        Args:
            schema: JSON schema.
        
        Returns:
            Dictionary with title, description, etc.
        """
        return {
            "title": schema.get("title", "Settings"),
            "description": schema.get("description", ""),
            "required": schema.get("required", []),
            "properties": schema.get("properties", {})
        }