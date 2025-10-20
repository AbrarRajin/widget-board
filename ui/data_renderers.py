"""Renders structured plugin data into Qt widgets."""
from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QColor
from enum import Enum


class CardLayout(Enum):
    """Standard card layout types."""
    TEXT = "text"  # Simple text display
    METRIC = "metric"  # Large number with label
    LIST = "list"  # Vertical list of items
    KEY_VALUE = "key_value"  # Key-value pairs
    HEADER_BODY = "header_body"  # Header with body content
    IMAGE_TEXT = "image_text"  # Image with text overlay


class DataRenderer:
    """Factory for creating UI from structured data."""
    
    @staticmethod
    def render(data: Dict[str, Any], parent: Optional[QWidget] = None) -> QWidget:
        """
        Render data based on layout type.
        
        Expected data structure:
        {
            "layout": "text" | "metric" | "list" | "key_value" | "header_body",
            "content": {...}  # Layout-specific content
        }
        """
        layout_type = data.get("layout", "text")
        content = data.get("content", {})
        
        if layout_type == "text":
            return DataRenderer._render_text(content, parent)
        elif layout_type == "metric":
            return DataRenderer._render_metric(content, parent)
        elif layout_type == "list":
            return DataRenderer._render_list(content, parent)
        elif layout_type == "key_value":
            return DataRenderer._render_key_value(content, parent)
        elif layout_type == "header_body":
            return DataRenderer._render_header_body(content, parent)
        else:
            return DataRenderer._render_error(f"Unknown layout: {layout_type}", parent)
    
    @staticmethod
    def _render_text(content: Dict[str, Any], parent: Optional[QWidget]) -> QWidget:
        """
        Render simple text.
        Expected: {"text": str, "align": "left"|"center"|"right", "size": int}
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        label = QLabel(content.get("text", ""))
        label.setWordWrap(True)
        
        # Alignment
        align = content.get("align", "left")
        if align == "center":
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif align == "right":
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Font size
        size = content.get("size", 12)
        font = label.font()
        font.setPointSize(size)
        label.setFont(font)
        
        layout.addWidget(label)
        return widget
    
    @staticmethod
    def _render_metric(content: Dict[str, Any], parent: Optional[QWidget]) -> QWidget:
        """
        Render large metric with label.
        Expected: {"value": str, "label": str, "unit": str, "color": str}
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        
        # Large value
        value_label = QLabel(str(content.get("value", "—")))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(36)
        value_font.setWeight(QFont.Weight.Bold)
        value_label.setFont(value_font)
        
        # Color
        color = content.get("color", "#333333")
        value_label.setStyleSheet(f"color: {color};")
        
        # Unit (if any)
        unit = content.get("unit", "")
        if unit:
            value_label.setText(f"{content.get('value', '—')} {unit}")
        
        # Label
        label_text = QLabel(content.get("label", ""))
        label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_font = QFont()
        label_font.setPointSize(11)
        label_text.setFont(label_font)
        label_text.setStyleSheet("color: #666;")
        
        layout.addStretch()
        layout.addWidget(value_label)
        layout.addWidget(label_text)
        layout.addStretch()
        
        return widget
    
    @staticmethod
    def _render_list(content: Dict[str, Any], parent: Optional[QWidget]) -> QWidget:
        """
        Render vertical list.
        Expected: {"items": [{"text": str, "secondary": str}], "max_items": int}
        """
        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        items = content.get("items", [])
        max_items = content.get("max_items", 10)
        
        for item in items[:max_items]:
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 8, 8, 8)
            item_layout.setSpacing(2)
            
            # Primary text
            primary = QLabel(item.get("text", ""))
            primary.setWordWrap(True)
            font = primary.font()
            font.setPointSize(11)
            primary.setFont(font)
            item_layout.addWidget(primary)
            
            # Secondary text (optional)
            if "secondary" in item:
                secondary = QLabel(item["secondary"])
                secondary.setWordWrap(True)
                sec_font = secondary.font()
                sec_font.setPointSize(9)
                secondary.setFont(sec_font)
                secondary.setStyleSheet("color: #666;")
                item_layout.addWidget(secondary)
            
            # Separator
            item_widget.setStyleSheet("QWidget { background: white; border-radius: 4px; }")
            layout.addWidget(item_widget)
        
        layout.addStretch()
        scroll.setWidget(container)
        return scroll
    
    @staticmethod
    def _render_key_value(content: Dict[str, Any], parent: Optional[QWidget]) -> QWidget:
        """
        Render key-value pairs.
        Expected: {"pairs": [{"key": str, "value": str}]}
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        pairs = content.get("pairs", [])
        
        for pair in pairs:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            key_label = QLabel(pair.get("key", ""))
            key_font = key_label.font()
            key_font.setWeight(QFont.Weight.Bold)
            key_label.setFont(key_font)
            key_label.setStyleSheet("color: #666;")
            
            value_label = QLabel(str(pair.get("value", "")))
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setWordWrap(True)
            
            row_layout.addWidget(key_label)
            row_layout.addStretch()
            row_layout.addWidget(value_label, 1)
            
            layout.addWidget(row)
        
        layout.addStretch()
        return widget
    
    @staticmethod
    def _render_header_body(content: Dict[str, Any], parent: Optional[QWidget]) -> QWidget:
        """
        Render header with body content.
        Expected: {"header": str, "body": str}
        """
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel(content.get("header", ""))
        header_font = header.font()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Body
        body = QLabel(content.get("body", ""))
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(body)
        layout.addStretch()
        
        return widget
    
    @staticmethod
    def _render_error(message: str, parent: Optional[QWidget]) -> QWidget:
        """Render error message."""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        label = QLabel(f"⚠ {message}")
        label.setWordWrap(True)
        label.setStyleSheet("color: #F44336;")
        layout.addWidget(label)
        layout.addStretch()
        
        return widget