"""Links widget plugin implementation."""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from core.plugin_api import PluginBase


class LinksPlugin(PluginBase):
    """A widget that displays a list of clickable links."""
    
    def __init__(self) -> None:
        """Initialize the links plugin."""
        super().__init__()
        self._widget: QWidget | None = None
        self._links_container: QWidget | None = None
        self._links_layout: QVBoxLayout | None = None
    
    def get_widget(self) -> QWidget:
        """Create and return the links widget.
        
        Returns:
            QWidget with links display.
        """
        if self._widget is not None:
            return self._widget
        
        # Create main widget
        self._widget = QWidget()
        main_layout = QVBoxLayout(self._widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Title label
        title = QLabel(self.settings.get("title", "Quick Links"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Scroll area for links
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Links container
        self._links_container = QWidget()
        self._links_layout = QVBoxLayout(self._links_container)
        self._links_layout.setSpacing(3)
        self._links_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(self._links_container)
        main_layout.addWidget(scroll, 1)
        
        # Build links
        self._build_links()
        
        return self._widget
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update links with new settings.
        
        Args:
            settings: New settings dictionary.
        """
        super().update(settings)
        self._build_links()
    
    def _build_links(self) -> None:
        """Build the list of link buttons from settings."""
        if not self._links_layout:
            return
        
        # Clear existing links
        while self._links_layout.count():
            item = self._links_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get links from settings
        links: List[Dict[str, str]] = self.settings.get("links", [])
        
        if not links:
            # Show placeholder
            label = QLabel("No links configured\n\nEdit settings to add links")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #888888;")
            self._links_layout.addWidget(label)
            return
        
        # Create button for each link
        for link_data in links:
            name = link_data.get("name", "Unnamed Link")
            url = link_data.get("url", "")
            
            if not url:
                continue
            
            button = QPushButton(name)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #106EBE;
                }
                QPushButton:pressed {
                    background-color: #005A9E;
                }
            """)
            
            # Connect click handler
            button.clicked.connect(lambda checked=False, u=url: self._open_link(u))
            
            self._links_layout.addWidget(button)
        
        # Add stretch at the end
        self._links_layout.addStretch()
    
    def _open_link(self, url: str) -> None:
        """Open a link in the default browser.
        
        Args:
            url: URL to open.
        """
        QDesktopServices.openUrl(QUrl(url))
