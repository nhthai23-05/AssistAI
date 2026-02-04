"""Chat panel component for calendar natural language commands"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal


class ChatPanel(QFrame):
    """Panel chat để nhập lệnh natural language cho calendar"""
    
    message_sent = pyqtSignal(str)  # Signal khi user gửi message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatSection")
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI cho chat panel"""
        layout = QVBoxLayout(self)
        
        # Title
        chat_title = QLabel("💬 AI Assistant - Natural Language Commands")
        chat_title.setObjectName("chatTitle")
        layout.addWidget(chat_title)
        
        # Examples
        examples = QLabel(
            "<i>Examples: 'Create meeting tomorrow 3pm' | "
            "'Move client call to Friday 2pm' | "
            "'Delete meeting on Monday'</i>"
        )
        examples.setWordWrap(True)
        layout.addWidget(examples)
        
        # Chat history (mini)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMaximumHeight(100)
        layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your command here...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
    
    def send_message(self):
        """Gửi message và emit signal"""
        user_message = self.chat_input.text().strip()
        if not user_message:
            return
        
        # Display user message
        self.add_message(f"You: {user_message}")
        self.chat_input.clear()
        
        # Emit signal
        self.message_sent.emit(user_message)
    
    def add_message(self, message):
        """Thêm message vào chat history"""
        self.chat_history.append(message)
    
    def set_processing(self, is_processing):
        """Enable/disable input khi đang xử lý"""
        self.chat_input.setEnabled(not is_processing)
        self.send_btn.setEnabled(not is_processing)
        
        if is_processing:
            self.add_message("AI: Processing...")
    
    def remove_last_message(self):
        """Xóa message cuối (dùng để xóa 'Processing...')"""
        text = self.chat_history.toPlainText()
        lines = text.split('\n')
        if lines:
            lines = lines[:-1]
            self.chat_history.setPlainText('\n'.join(lines))
    
    def clear_history(self):
        """Xóa toàn bộ chat history"""
        self.chat_history.clear()
        self.chat_input.clear()
