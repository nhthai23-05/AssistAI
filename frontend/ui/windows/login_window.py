"""Login Window - Full-screen login page displayed before main app"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LoginWindow(QWidget):
    """Màn hình login - hiển thị trước khi vào app"""
    login_success = pyqtSignal()  # Signal khi login thành công
    
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.init_ui()
    
    def init_ui(self):
        """Tạo UI cho login screen"""
        self.setWindowTitle("AssistAI - Login")
        self.setMinimumSize(500, 600)
        
        # Main layout với centering
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        
        # Spacer để đẩy content xuống giữa
        main_layout.addStretch()
        
        # Content container
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(30)
        
        # Logo/Icon
        logo = QLabel("🤖")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 100px;")
        content_layout.addWidget(logo)
        
        # App name
        app_name = QLabel("AssistAI")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        app_name.setFont(font)
        app_name.setStyleSheet("color: #2196F3;")
        content_layout.addWidget(app_name)
        
        # Description
        desc = QLabel("Your AI-powered productivity assistant")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 16px; color: #666;")
        content_layout.addWidget(desc)
        
        content_layout.addSpacing(40)
        
        # Login button
        login_btn = QPushButton("🔐 Login with Google")
        login_btn.setMinimumHeight(55)
        login_btn.setMinimumWidth(280)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 27px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #357AE8;
            }
            QPushButton:pressed {
                background-color: #2A5DC7;
            }
        """)
        login_btn.clicked.connect(self.handle_login)
        content_layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addLayout(content_layout)
        
        # Spacer để đẩy content lên giữa
        main_layout.addStretch()
    
    def handle_login(self):
        """Xử lý login"""
        try:
            from ui.dialogs.login_dialog import LoginDialog
            
            dialog = LoginDialog(self)
            if dialog.exec():
                # Login thành công
                self.login_success.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {e}")
