from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from services.calendar_service import CalendarService
from utils.threads import ChatThread

class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.calendar_service = CalendarService()
        
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Header
        title = QLabel("💬 AI Calendar Assistant")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Chat history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText(
            "AI Assistant will help you manage calendar with natural language.\n\n"
            "Examples:\n"
            "- 'Create meeting with team tomorrow at 3pm'\n"
            "- 'Change my dentist appointment to Friday 10am'\n"
            "- 'Delete the meeting on Monday'"
        )
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your request here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Add welcome message
        self.add_message("AI", "Hello! I'm your calendar assistant. How can I help you today?")
    
    def send_message(self):
        """Gửi message đến AI"""
        user_message = self.input_field.text().strip()
        if not user_message:
            return
        
        # Display user message
        self.add_message("You", user_message)
        self.input_field.clear()
        
        # Disable input khi đang xử lý
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.add_message("AI", "Processing...")
        
        # Gọi API trong thread riêng
        self.chat_thread = ChatThread(self.calendar_service, user_message)
        self.chat_thread.response_received.connect(self.on_response)
        self.chat_thread.error_occurred.connect(self.on_error)
        self.chat_thread.finished.connect(self.on_finished)
        self.chat_thread.start()
    
    def on_response(self, response):
        """Callback khi nhận được response"""
        self.remove_last_message()  # Xóa "Processing..."
        self.add_message("AI", response)
    
    def on_error(self, error):
        """Callback khi có lỗi"""
        self.remove_last_message()  # Xóa "Processing..."
        self.add_message("AI", f"❌ Error: {error}")
    
    def on_finished(self):
        """Callback khi thread hoàn thành"""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
    
    def add_message(self, sender, message):
        """Thêm message vào chat display"""
        formatted = f"<b>{sender}:</b> {message}<br>"
        self.chat_display.append(formatted)
    
    def remove_last_message(self):
        """Xóa message cuối cùng (dùng để xóa "Processing...")"""
        text = self.chat_display.toHtml()
        # Simple approach: xóa dòng cuối
        lines = text.split('<br>')
        if len(lines) > 1:
            text = '<br>'.join(lines[:-2]) + '<br>'
            self.chat_display.setHtml(text)