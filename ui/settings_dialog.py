"""Settings dialog for individual widget instances."""

import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QDialogButtonBox, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt

from core.schema_loader import SchemaLoader
from ui.settings_form_builder import SettingsFormBuilder

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Dialog for editing widget instance settings."""
    
    def __init__(
        self,
        schema: Dict[str, Any],
        current_settings: Dict[str, Any],
        title: str = "Widget Settings",
        parent=None
    ) -> None:
        """Initialize settings dialog.
        
        Args:
            schema: JSON Schema for the settings.
            current_settings: Current settings values.
            title: Dialog title.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.schema = schema
        self.current_settings = current_settings.copy()
        self.schema_loader = SchemaLoader()
        self.form_builder = SettingsFormBuilder()
        
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Build form from schema
        self.form_widget = self.form_builder.build_form(self.schema, self.current_settings)
        scroll_area.setWidget(self.form_widget)
        
        layout.addWidget(scroll_area, 1)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._on_restore_defaults
        )
        
        layout.addWidget(button_box)
    
    def _on_accept(self) -> None:
        """Handle OK button - validate and accept."""
        # Get values from form
        values = self.form_builder.get_values()
        
        # Validate against schema
        is_valid, error_msg = self.schema_loader.validate_data(values, self.schema)
        
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                f"Settings validation failed:\n\n{error_msg}"
            )
            return
        
        self.current_settings = values
        self.accept()
    
    def _on_restore_defaults(self) -> None:
        """Restore default values from schema."""
        defaults = self.schema_loader.get_default_values(self.schema)
        
        # Rebuild form with defaults
        self.form_widget.deleteLater()
        self.form_widget = self.form_builder.build_form(self.schema, defaults)
        
        # Update scroll area
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.setWidget(self.form_widget)
        
        logger.info("Restored default settings")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings values.
        
        Returns:
            Dictionary of settings.
        """
        return self.current_settings