"""Global application settings dialog."""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QSpinBox, QComboBox, QCheckBox, QGroupBox, QLabel
)
from PySide6.QtCore import Qt

from core.config import Config

logger = logging.getLogger(__name__)


class AppSettingsDialog(QDialog):
    """Dialog for global application settings."""
    
    def __init__(self, config: Config, parent=None) -> None:
        """Initialize app settings dialog.
        
        Args:
            config: Application configuration.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.config = config
        
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(500)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Grid group
        grid_group = QGroupBox("Grid Settings")
        grid_layout = QFormLayout()
        
        self.grid_rows_spin = QSpinBox()
        self.grid_rows_spin.setMinimum(4)
        self.grid_rows_spin.setMaximum(16)
        self.grid_rows_spin.setValue(8)
        self.grid_rows_spin.setEnabled(False)  # Fixed for M2
        grid_layout.addRow("Grid Rows:", self.grid_rows_spin)
        
        self.grid_cols_spin = QSpinBox()
        self.grid_cols_spin.setMinimum(4)
        self.grid_cols_spin.setMaximum(16)
        self.grid_cols_spin.setValue(8)
        self.grid_cols_spin.setEnabled(False)  # Fixed for M2
        grid_layout.addRow("Grid Columns:", self.grid_cols_spin)
        
        grid_note = QLabel("Note: Grid size is fixed at 8×8 in this version.")
        grid_note.setStyleSheet("color: #666; font-style: italic;")
        grid_layout.addRow("", grid_note)
        
        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)
        
        # Window group
        window_group = QGroupBox("Window")
        window_layout = QFormLayout()
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setMinimum(800)
        self.window_width_spin.setMaximum(4000)
        self.window_width_spin.setSingleStep(100)
        window_layout.addRow("Default Width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setMinimum(600)
        self.window_height_spin.setMaximum(3000)
        self.window_height_spin.setSingleStep(100)
        window_layout.addRow("Default Height:", self.window_height_spin)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Advanced group
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout()
        
        self.dev_mode_check = QCheckBox()
        self.dev_mode_check.setEnabled(False)  # Read-only for now
        advanced_layout.addRow("Developer Mode:", self.dev_mode_check)
        
        dev_note = QLabel("Set WIDGETBOARD_DEV=true environment variable to enable.")
        dev_note.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")
        advanced_layout.addRow("", dev_note)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _load_settings(self) -> None:
        """Load current settings into form."""
        # Theme
        theme_index = self.theme_combo.findData(self.config.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        # Window size
        self.window_width_spin.setValue(self.config.window_width)
        self.window_height_spin.setValue(self.config.window_height)
        
        # Grid
        self.grid_rows_spin.setValue(self.config.grid_rows)
        self.grid_cols_spin.setValue(self.config.grid_cols)
        
        # Dev mode
        self.dev_mode_check.setChecked(self.config.dev_mode)
    
    def _on_accept(self) -> None:
        """Save settings and close."""
        # Update config
        self.config.theme = self.theme_combo.currentData()
        self.config.window_width = self.window_width_spin.value()
        self.config.window_height = self.window_height_spin.value()
        self.config.grid_rows = self.grid_rows_spin.value()
        self.config.grid_cols = self.grid_cols_spin.value()
        
        # Save to file
        self.config.save_settings()
        
        logger.info("Application settings saved")
        self.accept()