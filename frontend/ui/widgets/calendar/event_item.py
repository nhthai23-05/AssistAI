"""Event item component - displays a single calendar event"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from datetime import datetime


class EventItem(QFrame):
    """Widget hiển thị 1 event trong calendar"""
    
    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.event = event
        self.setObjectName("eventItem")
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI cho event item"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Time
        start_str = self.event.get('start', {}).get('dateTime', '')
        if start_str and 'T' in start_str:
            time = datetime.fromisoformat(start_str.replace('Z', '+00:00')).strftime('%H:%M')
            time_label = QLabel(f"<b>{time}</b>")
        else:
            time_label = QLabel("<b>All day</b>")
        
        layout.addWidget(time_label)
        
        # Summary
        summary = self.event.get('summary', 'No title')
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(summary_label)
        
        # Location (if any)
        location = self.event.get('location')
        if location:
            loc_label = QLabel(f"📍 {location}")
            loc_label.setStyleSheet("font-size: 10px; color: #666;")
            layout.addWidget(loc_label)
