from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QScrollArea, QGridLayout,
    QFrame, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime, timedelta
from services.calendar_service import CalendarService

class ChatThread(QThread):
    """Thread để gọi API không block UI"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, calendar_service, user_message):
        super().__init__()
        self.calendar_service = calendar_service
        self.user_message = user_message
    
    def run(self):
        try:
            # Gọi smart-action - backend tự detect và xử lý
            result = self.calendar_service.smart_action(self.user_message)
            
            action = result.get('action', 'unknown')
            if action == 'create':
                response = f"✅ Created: {result.get('event', {}).get('summary', 'Event')}"
            elif action == 'update':
                response = f"✅ Updated: {result.get('reasoning', 'Event updated')}"
            elif action == 'delete':
                response = f"✅ Deleted: {result.get('deleted_event', 'Event')}"
            else:
                response = f"✅ {result.get('message', 'Done')}"
            
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.calendar_service = CalendarService()
        self.events = []
        
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI với week view và chat"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📅 Week Calendar View")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_events)
        header.addWidget(refresh_btn)
        
        main_layout.addLayout(header)
        
        # Week Calendar Grid
        calendar_frame = QFrame()
        calendar_frame.setObjectName("calendarFrame")
        calendar_layout = QVBoxLayout(calendar_frame)
        
        # Grid cho 7 ngày
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(10)
        
        # Tạo 7 cột cho 7 ngày
        self.day_columns = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(7):
            day = today + timedelta(days=i)
            day_widget = self.create_day_column(day, i)
            self.calendar_grid.addWidget(day_widget, 0, i)
            self.day_columns.append(day_widget)
        
        calendar_layout.addLayout(self.calendar_grid)
        main_layout.addWidget(calendar_frame)
        
        # Chat section
        chat_section = self.create_chat_section()
        main_layout.addWidget(chat_section)
    
    def create_day_column(self, day, column_index):
        """Tạo cột cho mỗi ngày"""
        day_widget = QFrame()
        day_widget.setObjectName("dayColumn")
        day_widget.setMinimumWidth(150)
        day_layout = QVBoxLayout(day_widget)
        
        # Header ngày
        day_name = day.strftime("%a")
        day_date = day.strftime("%d/%m")
        
        # Highlight hôm nay
        is_today = day.date() == datetime.now().date()
        header_text = f"<b>{day_name}</b><br>{day_date}"
        if is_today:
            header_text = f"<span style='color: #2196F3;'><b>TODAY</b><br>{day_date}</span>"
        
        day_header = QLabel(header_text)
        day_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_header.setObjectName("dayHeader")
        day_layout.addWidget(day_header)
        
        # Scroll area cho events
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        
        events_container = QWidget()
        events_layout = QVBoxLayout(events_container)
        events_layout.setSpacing(5)
        events_layout.addStretch()
        
        scroll.setWidget(events_container)
        day_layout.addWidget(scroll)
        
        # Lưu reference
        day_widget.events_layout = events_layout
        day_widget.day_date = day.date()
        
        return day_widget
    
    def create_chat_section(self):
        """Tạo chat section"""
        chat_frame = QFrame()
        chat_frame.setObjectName("chatSection")
        chat_layout = QVBoxLayout(chat_frame)
        
        # Title
        chat_title = QLabel("💬 AI Assistant - Natural Language Commands")
        chat_title.setObjectName("chatTitle")
        chat_layout.addWidget(chat_title)
        
        # Examples
        examples = QLabel(
            "<i>Examples: 'Create meeting tomorrow 3pm' | "
            "'Move client call to Friday 2pm' | "
            "'Delete meeting on Monday'</i>"
        )
        examples.setWordWrap(True)
        chat_layout.addWidget(examples)
        
        # Chat history (mini)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMaximumHeight(100)
        chat_layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your command here...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addLayout(input_layout)
        
        return chat_frame
    
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
        # Clear tất cả events trong các cột
        for day_widget in self.day_columns:
            # Xóa tất cả event items (giữ lại stretch)
            layout = day_widget.events_layout
            while layout.count() > 1:  # Giữ lại stretch item cuối
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Group events theo ngày
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
        
        # Thêm events vào các cột tương ứng
        for day_widget in self.day_columns:
            day_date = day_widget.day_date
            day_events = events_by_day.get(day_date, [])
            
            layout = day_widget.events_layout
            
            if not day_events:
                no_events = QLabel("<i>No events</i>")
                no_events.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_events.setStyleSheet("color: #999; padding: 10px;")
                layout.insertWidget(0, no_events)
            else:
                for event in day_events:
                    event_widget = self.create_event_widget(event)
                    layout.insertWidget(layout.count() - 1, event_widget)
    
    def create_event_widget(self, event):
        """Tạo widget hiển thị event"""
        event_frame = QFrame()
        event_frame.setObjectName("eventItem")
        event_layout = QVBoxLayout(event_frame)
        event_layout.setContentsMargins(5, 5, 5, 5)
        event_layout.setSpacing(2)
        
        # Time
        start_str = event.get('start', {}).get('dateTime', '')
        if start_str and 'T' in start_str:
            time = datetime.fromisoformat(start_str.replace('Z', '+00:00')).strftime('%H:%M')
            time_label = QLabel(f"<b>{time}</b>")
        else:
            time_label = QLabel("<b>All day</b>")
        
        event_layout.addWidget(time_label)
        
        # Summary
        summary = event.get('summary', 'No title')
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-size: 12px;")
        event_layout.addWidget(summary_label)
        
        # Location (if any)
        location = event.get('location')
        if location:
            loc_label = QLabel(f"📍 {location}")
            loc_label.setStyleSheet("font-size: 10px; color: #666;")
            event_layout.addWidget(loc_label)
        
        return event_frame
    
    def send_chat_message(self):
        """Gửi message đến AI để xử lý"""
        user_message = self.chat_input.text().strip()
        if not user_message:
            return
        
        # Display user message
        self.add_chat_message(f"You: {user_message}")
        self.chat_input.clear()
        
        # Disable input
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.add_chat_message("AI: Processing...")
        
        # Gọi API - backend tự detect action
        self.chat_thread = ChatThread(self.calendar_service, user_message)
        self.chat_thread.response_received.connect(self.on_chat_response)
        self.chat_thread.error_occurred.connect(self.on_chat_error)
        self.chat_thread.finished.connect(self.on_chat_finished)
        self.chat_thread.start()
    
    def add_chat_message(self, message):
        """Thêm message vào chat history"""
        self.chat_history.append(message)
    
    def on_chat_response(self, response):
        """Callback khi nhận response"""
        # Xóa "Processing..."
        text = self.chat_history.toPlainText()
        lines = text.split('\n')
        if lines and 'Processing' in lines[-1]:
            lines = lines[:-1]
            self.chat_history.setPlainText('\n'.join(lines))
        
        self.add_chat_message(f"AI: {response}")
        
        # Reload events
        self.load_events()
    
    def on_chat_error(self, error):
        """Callback khi có lỗi"""
        # Xóa "Processing..."
        text = self.chat_history.toPlainText()
        lines = text.split('\n')
        if lines and 'Processing' in lines[-1]:
            lines = lines[:-1]
            self.chat_history.setPlainText('\n'.join(lines))
        
        self.add_chat_message(f"AI: ❌ Error: {error}")
    
    def on_chat_finished(self):
        """Callback khi thread hoàn thành"""
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.chat_input.setFocus()