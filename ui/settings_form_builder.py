"""Settings form builder that generates Qt forms from JSON Schema."""

import logging
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QTextEdit, QLabel, QVBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsFormBuilder:
    """Builds Qt forms dynamically from JSON Schema."""
    
    def __init__(self) -> None:
        """Initialize form builder."""
        self.widgets: Dict[str, QWidget] = {}
    
    def build_form(self, schema: Dict[str, Any], initial_values: Optional[Dict[str, Any]] = None) -> QWidget:
        """Build a form widget from a JSON Schema.
        
        Args:
            schema: JSON Schema definition.
            initial_values: Initial values for form fields.
        
        Returns:
            QWidget containing the form.
        """
        if initial_values is None:
            initial_values = {}
        
        self.widgets.clear()
        
        # Create main widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add title and description if present
        if "title" in schema:
            title_label = QLabel(f"<h3>{schema['title']}</h3>")
            layout.addWidget(title_label)
        
        if "description" in schema:
            desc_label = QLabel(schema["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
            layout.addWidget(desc_label)
        
        # Create form layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Build fields for each property
        for key, prop_schema in properties.items():
            field_widget = self._create_field_widget(key, prop_schema, initial_values.get(key), required)
            if field_widget:
                label_text = prop_schema.get("title", key)
                if key in required:
                    label_text += " *"
                
                # Special handling for textarea - give it full width
                if isinstance(field_widget, QTextEdit):
                    # Add label on its own row
                    label = QLabel(label_text)
                    form_layout.addRow(label)
                    
                    # Add description if present
                    description = prop_schema.get("description", "")
                    if description:
                        desc_label = QLabel(description)
                        desc_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                        desc_label.setWordWrap(True)
                        form_layout.addRow(desc_label)
                    
                    # Add textarea on its own row spanning both columns
                    form_layout.addRow(field_widget)
                else:
                    # Normal form row for other widgets
                    form_layout.addRow(label_text, field_widget)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        return widget
    
    def _create_field_widget(
        self, 
        key: str, 
        prop_schema: Dict[str, Any], 
        initial_value: Any,
        required: List[str]
    ) -> Optional[QWidget]:
        """Create a widget for a single schema property.
        
        Args:
            key: Property key.
            prop_schema: Property schema definition.
            initial_value: Initial value for the field.
            required: List of required field keys.
        
        Returns:
            QWidget for the field, or None if type not supported.
        """
        field_type = prop_schema.get("type")
        description = prop_schema.get("description", "")
        
        widget: Optional[QWidget] = None
        
        if field_type == "string":
            if "enum" in prop_schema:
                # Dropdown for enum
                widget = self._create_enum_widget(prop_schema, initial_value)
            elif prop_schema.get("format") == "textarea":
                # Multi-line text
                widget = self._create_textarea_widget(prop_schema, initial_value)
            else:
                # Single-line text
                widget = self._create_string_widget(prop_schema, initial_value)
        
        elif field_type == "integer":
            widget = self._create_integer_widget(prop_schema, initial_value)
        
        elif field_type == "number":
            widget = self._create_number_widget(prop_schema, initial_value)
        
        elif field_type == "boolean":
            widget = self._create_boolean_widget(prop_schema, initial_value)
        
        else:
            logger.warning("Unsupported field type: %s for key: %s", field_type, key)
            widget = QLabel(f"[Unsupported type: {field_type}]")
        
        if widget:
            # Set tooltip from description
            if description:
                widget.setToolTip(description)
            
            # Ensure widgets have proper minimum sizes for visibility
            if isinstance(widget, QCheckBox):
                widget.setMinimumHeight(25)
                widget.setMinimumWidth(200)
            elif isinstance(widget, QTextEdit):
                widget.setMinimumHeight(80)
                widget.setMinimumWidth(300)
            elif isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                widget.setMinimumWidth(200)
            
            # Store widget reference
            self.widgets[key] = widget
        
        return widget
    
    def _create_string_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QLineEdit:
        """Create a string input widget."""
        widget = QLineEdit()
        
        if initial_value is not None:
            widget.setText(str(initial_value))
        elif "default" in prop_schema:
            widget.setText(str(prop_schema["default"]))
        
        if "maxLength" in prop_schema:
            widget.setMaxLength(prop_schema["maxLength"])
        
        if "pattern" in prop_schema:
            widget.setPlaceholderText(f"Pattern: {prop_schema['pattern']}")
        
        return widget
    
    def _create_textarea_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QTextEdit:
        """Create a multi-line text widget."""
        widget = QTextEdit()
        widget.setMinimumHeight(80)
        widget.setMaximumHeight(150)
        
        if initial_value is not None:
            widget.setPlainText(str(initial_value))
        elif "default" in prop_schema:
            widget.setPlainText(str(prop_schema["default"]))
        
        return widget
    
    def _create_integer_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QSpinBox:
        """Create an integer input widget."""
        widget = QSpinBox()
        
        if "minimum" in prop_schema:
            widget.setMinimum(prop_schema["minimum"])
        else:
            widget.setMinimum(-2147483648)
        
        if "maximum" in prop_schema:
            widget.setMaximum(prop_schema["maximum"])
        else:
            widget.setMaximum(2147483647)
        
        if initial_value is not None:
            widget.setValue(int(initial_value))
        elif "default" in prop_schema:
            widget.setValue(prop_schema["default"])
        
        return widget
    
    def _create_number_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QDoubleSpinBox:
        """Create a number input widget."""
        widget = QDoubleSpinBox()
        
        if "minimum" in prop_schema:
            widget.setMinimum(prop_schema["minimum"])
        else:
            widget.setMinimum(-1e10)
        
        if "maximum" in prop_schema:
            widget.setMaximum(prop_schema["maximum"])
        else:
            widget.setMaximum(1e10)
        
        if "multipleOf" in prop_schema:
            widget.setSingleStep(prop_schema["multipleOf"])
        else:
            widget.setSingleStep(0.1)
        
        widget.setDecimals(2)
        
        if initial_value is not None:
            widget.setValue(float(initial_value))
        elif "default" in prop_schema:
            widget.setValue(prop_schema["default"])
        
        return widget
    
    def _create_boolean_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QCheckBox:
        """Create a boolean checkbox widget."""
        widget = QCheckBox()
        widget.setMinimumHeight(25)  # Ensure checkbox is visible
        
        if initial_value is not None:
            widget.setChecked(bool(initial_value))
        elif "default" in prop_schema:
            widget.setChecked(prop_schema["default"])
        
        return widget
    
    def _create_enum_widget(self, prop_schema: Dict[str, Any], initial_value: Any) -> QComboBox:
        """Create an enum dropdown widget."""
        widget = QComboBox()
        
        enum_values = prop_schema.get("enum", [])
        for value in enum_values:
            widget.addItem(str(value), value)
        
        if initial_value is not None:
            index = widget.findData(initial_value)
            if index >= 0:
                widget.setCurrentIndex(index)
        elif "default" in prop_schema:
            index = widget.findData(prop_schema["default"])
            if index >= 0:
                widget.setCurrentIndex(index)
        
        return widget
    
    def get_values(self) -> Dict[str, Any]:
        """Extract current values from all form widgets.
        
        Returns:
            Dictionary of field key -> value.
        """
        values = {}
        
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                values[key] = widget.toPlainText()
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()
        
        return values