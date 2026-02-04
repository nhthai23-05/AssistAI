from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.chat_service import ChatService
from utils.threads import ChatThread

class ChatWidget(QWidget):
    """Widget cho AI chat assistant"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_service = ChatService()
        self.conversation_history = []
        self.current_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat conversation will appear here...")
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Welcome message
        self.add_ai_message("Hello! I'm your calendar assistant. How can I help you today?")
    
    def send_message(self):
        """Gửi message từ user"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Hiển thị user message
        self.add_user_message(message)
        self.message_input.clear()
        
        # Lưu vào history
        self.conversation_history.append({
            'role': 'user',
            'content': message
        })
        
        # Disable input khi đang xử lý
        self.set_input_enabled(False)
        self.add_ai_message("Processing...")
        
        # Gọi API qua thread
        self.current_thread = ChatThread(
            self.chat_service,
            message,
            self.conversation_history
        )
        self.current_thread.response_received.connect(self.handle_response)
        self.current_thread.error_occurred.connect(self.handle_error)
        self.current_thread.start()
    
    def handle_response(self, response: str):
        """Xử lý response từ AI"""
        # Xóa "Processing..."
        self.remove_last_message()
        
        # Hiển thị AI response
        self.add_ai_message(response)
        
        # Lưu vào history
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        # Enable input
        self.set_input_enabled(True)
    
    def handle_error(self, error: str):
        """Xử lý lỗi"""
        self.remove_last_message()
        self.add_ai_message(f"❌ Error: {error}")
        self.set_input_enabled(True)
    
    def add_user_message(self, message: str):
        """Thêm user message vào chat display"""
        self.chat_display.append(f"<p style='color: #2196F3;'><b>You:</b> {message}</p>")
    
    def add_ai_message(self, message: str):
        """Thêm AI message vào chat display"""
        self.chat_display.append(f"<p style='color: #4CAF50;'><b>AI:</b> {message}</p>")
    
    def remove_last_message(self):
        """Xóa message cuối (dùng cho "Processing...")"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
    
    def set_input_enabled(self, enabled: bool):
        """Enable/disable input controls"""
        self.message_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)