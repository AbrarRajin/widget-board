"""Integration test for M5 components."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from ui.tile_widget import TileWidget
from ui.status_indicator import TileStatus
from core.update_manager import UpdateManager, ThrottleConfig
import logging

logging.basicConfig(level=logging.DEBUG)


class M5TestWindow(QMainWindow):
    """Test window for M5 components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M5 Test - Tile Chrome & Data Rendering")
        self.setGeometry(100, 100, 1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        
        # Create test tiles with different layouts
        
        # 1. Metric layout (clock-style)
        tile1 = TileWidget("clock_001", "Clock")
        tile1.setFixedSize(300, 250)
        tile1.set_status(TileStatus.OK)
        tile1.set_data({
            "layout": "metric",
            "content": {
                "value": "10:45:30",
                "label": "Monday, October 20, 2025",
                "color": "#2196F3"
            }
        })
        layout.addWidget(tile1)
        
        # 2. Key-value layout (personal info)
        tile2 = TileWidget("info_001", "Personal Info")
        tile2.setFixedSize(300, 250)
        tile2.set_status(TileStatus.OK)
        tile2.set_data({
            "layout": "key_value",
            "content": {
                "pairs": [
                    {"key": "Name", "value": "John Doe"},
                    {"key": "Email", "value": "john@example.com"},
                    {"key": "Phone", "value": "+1 234 567 8900"}
                ]
            }
        })
        layout.addWidget(tile2)
        
        # 3. List layout (links)
        tile3 = TileWidget("links_001", "Quick Links")
        tile3.setFixedSize(300, 300)
        tile3.set_status(TileStatus.UPDATING, "Loading")
        tile3.set_data({
            "layout": "list",
            "content": {
                "items": [
                    {"text": "GitHub", "secondary": "Development • https://github.com"},
                    {"text": "Gmail", "secondary": "Email • https://gmail.com"},
                    {"text": "Calendar", "secondary": "Productivity • https://calendar.google.com"}
                ]
            }
        })
        layout.addWidget(tile3)
        
        # Test update manager
        self.update_manager = UpdateManager()
        self.update_manager.update_dispatched.connect(self._on_update_dispatched)
        
        # Configure throttling
        config = ThrottleConfig(min_interval_ms=500, max_pending=2)
        self.update_manager.set_throttle_config("clock_001", config)
        
        # Simulate rapid updates
        for i in range(5):
            self.update_manager.request_update("clock_001", "timer")
        
        print("M5 Test Window Ready")
        print("- Metric layout (clock)")
        print("- Key-value layout (personal info)")
        print("- List layout (links)")
        print("- Update manager throttling test")
    
    def _on_update_dispatched(self, instance_id: str, reason: str):
        print(f"✓ Update dispatched: {instance_id} (reason: {reason})")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = M5TestWindow()
    window.show()
    sys.exit(app.exec())