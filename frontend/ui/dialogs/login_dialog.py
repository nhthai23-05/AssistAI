from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import webbrowser
from services.auth_service import AuthService
from config import API

class AuthCheckThread(QThread):
    """Thread để check auth status định kỳ"""
    authenticated = pyqtSignal()
    
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.running = True
    
    def run(self):
        """Check auth status mỗi 2 giây"""
        while self.running:
            try:
                result = self.auth_service.check_status()
                if result.get('authenticated'):
                    self.authenticated.emit()
                    break
            except:
                pass
            self.msleep(2000)  # 2 seconds
    
    def stop(self):
        self.running = False

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self.auth_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        self.setWindowTitle("Login with Google")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🔐 Google Authentication")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Click the button below to open your browser\n"
            "and login with your Google account.\n\n"
            "After authentication, this dialog will\n"
            "automatically close."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Login button
        self.login_btn = QPushButton("🌐 Open Browser to Login")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.clicked.connect(self.start_login)
        layout.addWidget(self.login_btn)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
    
    def start_login(self):
        """Bắt đầu quá trình login"""
        try:
            # Mở browser
            webbrowser.open(API.AUTH_LOGIN)
            
            # Disable button
            self.login_btn.setEnabled(False)
            self.progress.show()
            self.status_label.setText("Waiting for authentication...")
            
            # Bắt đầu check auth status
            self.auth_thread = AuthCheckThread(self.auth_service)
            self.auth_thread.authenticated.connect(self.on_authenticated)
            self.auth_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open browser: {e}")
            self.reset_ui()
    
    def on_authenticated(self):
        """Callback khi authentication thành công"""
        self.auth_thread.stop()
        self.status_label.setText("✅ Authentication successful!")
        
        QTimer.singleShot(1000, self.accept)  # Đóng dialog sau 1s
    
    def reset_ui(self):
        """Reset UI về trạng thái ban đầu"""
        self.login_btn.setEnabled(True)
        self.progress.hide()
        self.status_label.setText("")
    
    def closeEvent(self, event):
        """Cleanup khi đóng dialog"""
        if self.auth_thread and self.auth_thread.isRunning():
            self.auth_thread.stop()
            self.auth_thread.wait()
        event.accept()