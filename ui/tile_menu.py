"""Tile overflow menu with common actions."""
from typing import Optional, Callable
from PySide6.QtWidgets import QMenu, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction


class TileMenu(QPushButton):
    """Overflow menu button for tile actions."""
    
    settings_requested = Signal()
    refresh_requested = Signal()
    remove_requested = Signal()
    duplicate_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("⋮", parent)
        self.setFixedSize(24, 24)
        self.setToolTip("Tile options")
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                color: #666;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
                color: #333;
            }
            QPushButton:pressed {
                background: rgba(0, 0, 0, 0.1);
            }
        """)
        
        self._setup_menu()
        self.clicked.connect(self._show_menu)
    
    def _setup_menu(self) -> None:
        """Create the context menu."""
        self._menu = QMenu(self)
        
        settings_action = QAction("⚙ Settings...", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings_action)
        
        refresh_action = QAction("↻ Refresh", self)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        self._menu.addAction(refresh_action)
        
        self._menu.addSeparator()
        
        duplicate_action = QAction("⎘ Duplicate", self)
        duplicate_action.triggered.connect(self.duplicate_requested.emit)
        self._menu.addAction(duplicate_action)
        
        self._menu.addSeparator()
        
        remove_action = QAction("🗑 Remove", self)
        remove_action.triggered.connect(self.remove_requested.emit)
        self._menu.addAction(remove_action)
    
    def _show_menu(self) -> None:
        """Display the menu below the button."""
        self._menu.exec(self.mapToGlobal(self.rect().bottomLeft()))