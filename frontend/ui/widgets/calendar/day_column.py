"""Day column component - displays events for one day"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt6.QtCore import Qt
from datetime import datetime
from .event_item import EventItem


class DayColumn(QFrame):
    """Cột hiển thị events của 1 ngày"""
    
    def __init__(self, day, parent=None):
        super().__init__(parent)
        self.day = day
        self.day_date = day.date()
        self.setObjectName("dayColumn")
        self.setMinimumWidth(150)
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI cho day column"""
        layout = QVBoxLayout(self)
        
        # Header ngày
        day_name = self.day.strftime("%a")
        day_date = self.day.strftime("%d/%m")
        
        # Highlight hôm nay
        is_today = self.day_date == datetime.now().date()
        header_text = f"<b>{day_name}</b><br>{day_date}"
        if is_today:
            header_text = f"<span style='color: #2196F3;'><b>TODAY</b><br>{day_date}</span>"
        
        day_header = QLabel(header_text)
        day_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_header.setObjectName("dayHeader")
        layout.addWidget(day_header)
        
        # Scroll area cho events
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        
        events_container = QWidget()
        self.events_layout = QVBoxLayout(events_container)
        self.events_layout.setSpacing(5)
        self.events_layout.addStretch()
        
        scroll.setWidget(events_container)
        layout.addWidget(scroll)
    
    def set_events(self, events):
        """Hiển thị danh sách events"""
        # Clear old events
        self.clear_events()
        
        if not events:
            no_events = QLabel("<i>No events</i>")
            no_events.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_events.setStyleSheet("color: #999; padding: 10px;")
            self.events_layout.insertWidget(0, no_events)
        else:
            for event in events:
                event_widget = EventItem(event)
                self.events_layout.insertWidget(self.events_layout.count() - 1, event_widget)
    
    def clear_events(self):
        """Xóa tất cả events"""
        while self.events_layout.count() > 1:  # Giữ lại stretch item cuối
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
