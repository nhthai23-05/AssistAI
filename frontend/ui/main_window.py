from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from ui.login_dialog import LoginDialog
from ui.calendar_widget import CalendarWidget
from ui.chat_widget import ChatWidget
from services.auth_service import AuthService
from config import APP_NAME, ICONS_DIR

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.is_authenticated = False
        
        self.init_ui()
        self.check_auth_status()
    
    def init_ui(self):
        """Khởi tạo UI"""
        self.setWindowTitle(f"{APP_NAME} - Calendar Assistant")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.calendar_widget = CalendarWidget()
        self.chat_widget = ChatWidget()
        
        self.tabs.addTab(self.calendar_widget, "📅 Calendar")
        self.tabs.addTab(self.chat_widget, "💬 AI Assistant")
        
        main_layout.addWidget(self.tabs)
        
        # Disable tabs nếu chưa login
        self.tabs.setEnabled(False)
    
    def create_header(self) -> QWidget:
        """Tạo header với info và nút login/logout"""
        header = QWidget()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        
        # Logo và title
        title_label = QLabel(f"🤖 {APP_NAME}")
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Not logged in")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        
        # Login/Logout button
        self.auth_button = QPushButton("Login with Google")
        self.auth_button.setObjectName("authButton")
        self.auth_button.clicked.connect(self.toggle_auth)
        layout.addWidget(self.auth_button)
        
        return header
    
    def check_auth_status(self):
        """Kiểm tra trạng thái đăng nhập"""
        try:
            result = self.auth_service.check_status()
            self.is_authenticated = result.get('authenticated', False)
            self.update_ui_auth_state()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot connect to backend: {e}")
    
    def update_ui_auth_state(self):
        """Cập nhật UI theo trạng thái auth"""
        if self.is_authenticated:
            self.status_label.setText("✅ Logged in")
            self.auth_button.setText("Logout")
            self.tabs.setEnabled(True)
            
            # Load calendar events
            self.calendar_widget.load_events()
        else:
            self.status_label.setText("❌ Not logged in")
            self.auth_button.setText("Login with Google")
            self.tabs.setEnabled(False)
    
    def toggle_auth(self):
        """Xử lý login/logout"""
        if self.is_authenticated:
            self.logout()
        else:
            self.login()
    
    def login(self):
        """Mở dialog login"""
        dialog = LoginDialog(self)
        if dialog.exec():
            # Login thành công
            self.is_authenticated = True
            self.update_ui_auth_state()
    
    def logout(self):
        """Đăng xuất"""
        reply = QMessageBox.question(
            self, 
            "Logout", 
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auth_service.logout()
                self.is_authenticated = False
                self.update_ui_auth_state()
                QMessageBox.information(self, "Success", "Logged out successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Logout failed: {e}")