"""Personal information display plugin."""
from typing import Dict, Any
import json


class PersonalInfoPlugin:
    """Displays personal information in key-value format."""
    
    def __init__(self, instance_id: str, settings: Dict[str, Any]):
        self.instance_id = instance_id
        self.settings = settings
        
        # User-configured info
        self.info = settings.get("info", {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 234 567 8900",
            "location": "San Francisco, CA"
        })
    
    def get_update(self, reason: str) -> Dict[str, Any]:
        """Return personal info as key-value pairs."""
        pairs = [
            {"key": "Name", "value": self.info.get("name", "—")},
            {"key": "Email", "value": self.info.get("email", "—")},
            {"key": "Phone", "value": self.info.get("phone", "—")},
            {"key": "Location", "value": self.info.get("location", "—")}
        ]
        
        return {
            "status": "ok",
            "data": {
                "layout": "key_value",
                "content": {
                    "pairs": pairs
                }
            },
            "ttl_ms": 3600000  # Update every hour (static content)
        }


if __name__ == "__main__":
    plugin = PersonalInfoPlugin("info_001", {})
    update = plugin.get_update("user")
    print(json.dumps(update, indent=2))