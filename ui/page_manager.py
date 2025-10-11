"""Page manager for navigating between dashboard pages."""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QToolButton
)
from PySide6.QtCore import Qt, Signal

from core.models import Page

logger = logging.getLogger(__name__)


class PageManager(QWidget):
    """Widget for managing and navigating pages."""
    
    # Signals
    page_changed = Signal(Page)
    page_add_requested = Signal()
    page_remove_requested = Signal(Page)
    
    def __init__(self, parent=None) -> None:
        """Initialize page manager.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.pages: list[Page] = []
        self.current_page: Optional[Page] = None
        self.current_index = 0
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the page manager UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Previous button
        self.prev_btn = QToolButton()
        self.prev_btn.setText("◀")
        self.prev_btn.setToolTip("Previous Page")
        self.prev_btn.clicked.connect(self._on_previous)
        layout.addWidget(self.prev_btn)
        
        # Page indicator
        self.page_label = QLabel("No Pages")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(200)
        layout.addWidget(self.page_label, 1)
        
        # Next button
        self.next_btn = QToolButton()
        self.next_btn.setText("▶")
        self.next_btn.setToolTip("Next Page")
        self.next_btn.clicked.connect(self._on_next)
        layout.addWidget(self.next_btn)
        
        layout.addSpacing(20)
        
        # Add page button
        self.add_btn = QPushButton("+ New Page")
        self.add_btn.clicked.connect(self.page_add_requested.emit)
        layout.addWidget(self.add_btn)
        
        # Remove page button
        self.remove_btn = QPushButton("Remove Page")
        self.remove_btn.clicked.connect(self._on_remove_page)
        layout.addWidget(self.remove_btn)
        
        self._update_buttons()
    
    def set_pages(self, pages: list[Page]) -> None:
        """Set the available pages.
        
        Args:
            pages: List of pages.
        """
        self.pages = pages
        
        if self.pages:
            self.current_index = 0
            self.current_page = self.pages[0]
            self.page_changed.emit(self.current_page)
        else:
            self.current_index = 0
            self.current_page = None
        
        self._update_buttons()
        logger.info("Loaded %d pages", len(pages))
    
    def add_page(self, page: Page) -> None:
        """Add a new page.
        
        Args:
            page: Page to add.
        """
        self.pages.append(page)
        self.current_index = len(self.pages) - 1
        self.current_page = page
        self.page_changed.emit(page)
        self._update_buttons()
        logger.info("Added page: %s", page.name)
    
    def remove_current_page(self) -> None:
        """Remove the current page."""
        if not self.current_page or not self.pages:
            return
        
        removed_page = self.current_page
        self.pages.remove(self.current_page)
        
        # Navigate to previous or next page
        if self.pages:
            if self.current_index >= len(self.pages):
                self.current_index = len(self.pages) - 1
            self.current_page = self.pages[self.current_index]
            self.page_changed.emit(self.current_page)
        else:
            self.current_index = 0
            self.current_page = None
        
        self._update_buttons()
        self.page_remove_requested.emit(removed_page)
        logger.info("Removed page: %s", removed_page.name)
    
    def _on_previous(self) -> None:
        """Navigate to previous page."""
        if not self.pages:
            return
        
        self.current_index = (self.current_index - 1) % len(self.pages)
        self.current_page = self.pages[self.current_index]
        self.page_changed.emit(self.current_page)
        self._update_buttons()
    
    def _on_next(self) -> None:
        """Navigate to next page."""
        if not self.pages:
            return
        
        self.current_index = (self.current_index + 1) % len(self.pages)
        self.current_page = self.pages[self.current_index]
        self.page_changed.emit(self.current_page)
        self._update_buttons()
    
    def _on_remove_page(self) -> None:
        """Handle remove page button click."""
        if self.current_page:
            self.remove_current_page()
    
    def _update_buttons(self) -> None:
        """Update button states and page label."""
        has_pages = len(self.pages) > 0
        multiple_pages = len(self.pages) > 1
        
        self.prev_btn.setEnabled(multiple_pages)
        self.next_btn.setEnabled(multiple_pages)
        self.remove_btn.setEnabled(has_pages)
        
        if has_pages and self.current_page:
            self.page_label.setText(
                f"Page {self.current_index + 1} of {len(self.pages)}: {self.current_page.name}"
            )
        else:
            self.page_label.setText("No Pages")
