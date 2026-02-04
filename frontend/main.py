import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget
from PyQt6.QtGui import QIcon
from ui.windows.login_window import LoginWindow
from ui.windows.main_window import MainWindow
from services.auth_service import AuthService
from config import APP_NAME, APP_VERSION


class App(QStackedWidget):
    """Main app với 2 pages: Login và MainWindow"""
    
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)
        
        # Page 0: Login Window
        self.login_window = LoginWindow(self.auth_service)
        self.login_window.login_success.connect(self.show_main_window)
        self.addWidget(self.login_window)
        
        # Page 1: Main Window (tạo sau khi login)
        self.main_window = None
        
        # Kiểm tra authentication
        try:
            result = self.auth_service.check_status()
            is_authenticated = result.get('authenticated', False)
            
            if is_authenticated:
                self.show_main_window()
            else:
                self.setCurrentIndex(0)  # Hiển thị login
        except:
            self.setCurrentIndex(0)  # Hiển thị login nếu không kết nối được backend
    
    def show_main_window(self):
        """Chuyển sang main window sau khi login"""
        if self.main_window is None:
            self.main_window = MainWindow(self.auth_service)
            self.main_window.logout_signal.connect(self.handle_logout)
            self.addWidget(self.main_window)
        
        self.setCurrentIndex(1)  # Chuyển sang main window
    
    def handle_logout(self):
        """Xử lý logout - quay về login screen"""
        # Xóa main window cũ để clear dữ liệu
        if self.main_window:
            self.removeWidget(self.main_window)
            self.main_window.deleteLater()
            self.main_window = None
        
        # Tạo login window mới
        self.login_window = LoginWindow(self.auth_service)
        self.login_window.login_success.connect(self.show_main_window)
        self.insertWidget(0, self.login_window)
        
        self.setCurrentIndex(0)  # Hiển thị login


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Load styles
    try:
        with open('assets/styles/main.qss', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: Style file not found")
    
    # Tạo và hiển thị app
    window = App()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()