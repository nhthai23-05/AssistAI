"""Main Window - Main application window after login"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from services.auth_service import AuthService
from config import APP_NAME


class MainWindow(QMainWindow):
    """Main window của app - hiển thị sau khi login"""
    logout_signal = pyqtSignal()  # Signal khi user logout
    
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        
        self.init_ui()
        self.load_initial_data()
    
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
        
        # Import widgets here to avoid circular imports
        from ui.widgets.calendar_widget import CalendarWidget
        from ui.chat_widget import ChatWidget
        
        self.calendar_widget = CalendarWidget()
        self.chat_widget = ChatWidget()
        
        self.tabs.addTab(self.calendar_widget, "📅 Calendar")
        self.tabs.addTab(self.chat_widget, "💬 AI Assistant")
        
        main_layout.addWidget(self.tabs)
    
    def create_header(self) -> QWidget:
        """Tạo header với info và nút logout"""
        header = QWidget()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        
        # Logo và title
        title_label = QLabel(f"🤖 {APP_NAME}")
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Status label
        self.status_label = QLabel("✅ Logged in")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        
        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setObjectName("authButton")
        self.logout_button.clicked.connect(self.logout)
        layout.addWidget(self.logout_button)
        
        return header
    
    def load_initial_data(self):
        """Load dữ liệu ban đầu sau khi khởi tạo"""
        try:
            # Load calendar events
            self.calendar_widget.load_events()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot load initial data: {e}")
    
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
                self.logout_signal.emit()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Logout failed: {e}")
