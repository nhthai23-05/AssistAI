"""Calendar Widget - refactored to use modular components"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from services.calendar_service import CalendarService
from utils.threads import CalendarChatThread
from ui.widgets.calendar.day_column import DayColumn
from ui.widgets.calendar.chat_panel import ChatPanel


class CalendarWidget(QWidget):
    """Main calendar widget - orchestrates calendar components"""
    
    def __init__(self):
        super().__init__()
        self.calendar_service = CalendarService()
        self.events = []
        self.day_columns = []
        self.chat_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI với week view và chat"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header = self.create_header()
        main_layout.addLayout(header)
        
        # Week Calendar Grid
        calendar_frame = self.create_calendar_grid()
        main_layout.addWidget(calendar_frame)
        
        # Chat section
        self.chat_panel = ChatPanel()
        self.chat_panel.message_sent.connect(self.handle_chat_message)
        main_layout.addWidget(self.chat_panel)
    
    def create_header(self):
        """Tạo header với title và refresh button"""
        header = QHBoxLayout()
        
        title = QLabel("📅 Week Calendar View")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_events)
        header.addWidget(refresh_btn)
        
        return header
    
    def create_calendar_grid(self):
        """Tạo grid 7 ngày sử dụng DayColumn components"""
        calendar_frame = QFrame()
        calendar_frame.setObjectName("calendarFrame")
        layout = QVBoxLayout(calendar_frame)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(7):
            day = today + timedelta(days=i)
            day_column = DayColumn(day)
            grid.addWidget(day_column, 0, i)
            self.day_columns.append(day_column)
        
        layout.addLayout(grid)
        return calendar_frame
    
    def load_events(self):
        """Load events từ API và hiển thị theo ngày"""
        try:
            result = self.calendar_service.list_events()
            self.events = result.get('events', [])
            self.display_events()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot load events: {e}")
    
    def display_events(self):
        """Hiển thị events vào week calendar grid"""
        # Group events by date
        events_by_day = {}
        for event in self.events:
            start_str = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            if start_str:
                try:
                    if 'T' in start_str:
                        event_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
                    else:
                        event_date = datetime.fromisoformat(start_str).date()
                    
                    if event_date not in events_by_day:
                        events_by_day[event_date] = []
                    events_by_day[event_date].append(event)
                except:
                    pass
        
        # Set events cho từng day column
        for day_column in self.day_columns:
            day_events = events_by_day.get(day_column.day_date, [])
            day_column.set_events(day_events)
    
    def handle_chat_message(self, user_message):
        """Xử lý message từ chat panel"""
        # Set processing state
        self.chat_panel.set_processing(True)
        
        # Gọi API - backend tự detect action
        self.chat_thread = CalendarChatThread(self.calendar_service, user_message)
        self.chat_thread.response_received.connect(self.on_chat_response)
        self.chat_thread.error_occurred.connect(self.on_chat_error)
        self.chat_thread.finished.connect(self.on_chat_finished)
        self.chat_thread.start()
    
    def on_chat_response(self, response):
        """Callback khi nhận response"""
        # Xóa "Processing..."
        self.chat_panel.remove_last_message()
        
        # Add AI response
        self.chat_panel.add_message(f"AI: {response}")
        
        # Reload events
        self.load_events()
    
    def on_chat_error(self, error):
        """Callback khi có lỗi"""
        # Xóa "Processing..."
        self.chat_panel.remove_last_message()
        
        # Add error message
        self.chat_panel.add_message(f"AI: ❌ Error: {error}")
    
    def on_chat_finished(self):
        """Callback khi thread hoàn thành"""
        self.chat_panel.set_processing(False)
    
    def clear_data(self):
        """Xóa toàn bộ dữ liệu khi logout"""
        self.events = []
        self.chat_panel.clear_history()
        
        # Clear events trong calendar
        for day_column in self.day_columns:
            day_column.clear_events()
