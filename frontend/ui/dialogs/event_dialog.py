from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QDateTimeEdit, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import QDateTime, Qt
from datetime import datetime

class EventDialog(QDialog):
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self.event = event
        
        self.init_ui()
        
        if event:
            self.load_event_data()
    
    def init_ui(self):
        """Khởi tạo UI"""
        title = "Edit Event" if self.event else "Create New Event"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Meeting with team")
        form.addRow("Title*:", self.title_input)
        
        # Start datetime
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")
        form.addRow("Start*:", self.start_datetime)
        
        # End datetime
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1 hour
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")
        form.addRow("End*:", self.end_datetime)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Optional description")
        form.addRow("Description:", self.description_input)
        
        # Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Office, Room 101")
        form.addRow("Location:", self.location_input)
        
        # Attendees
        self.attendees_input = QLineEdit()
        self.attendees_input.setPlaceholderText("email1@gmail.com, email2@gmail.com")
        form.addRow("Attendees:", self.attendees_input)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.validate_and_accept)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
    
    def load_event_data(self):
        """Load dữ liệu event vào form"""
        self.title_input.setText(self.event.get('summary', ''))
        
        # Parse start datetime
        start_str = self.event.get('start', {}).get('dateTime', '')
        if start_str:
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            self.start_datetime.setDateTime(QDateTime(start_dt))
        
        # Parse end datetime
        end_str = self.event.get('end', {}).get('dateTime', '')
        if end_str:
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            self.end_datetime.setDateTime(QDateTime(end_dt))
        
        self.description_input.setText(self.event.get('description', ''))
        self.location_input.setText(self.event.get('location', ''))
        
        # Parse attendees
        attendees = self.event.get('attendees', [])
        emails = [a.get('email', '') for a in attendees]
        self.attendees_input.setText(', '.join(emails))
    
    def validate_and_accept(self):
        """Validate input trước khi accept"""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required!")
            return
        
        start = self.start_datetime.dateTime()
        end = self.end_datetime.dateTime()
        
        if start >= end:
            QMessageBox.warning(self, "Validation Error", "End time must be after start time!")
            return
        
        self.accept()
    
    def get_event_data(self):
        """Lấy dữ liệu từ form"""
        start_dt = self.start_datetime.dateTime().toPyDateTime()
        end_dt = self.end_datetime.dateTime().toPyDateTime()
        
        data = {
            'summary': self.title_input.text().strip(),
            'start_datetime': start_dt.isoformat(),
            'end_datetime': end_dt.isoformat(),
        }
        
        # Optional fields
        description = self.description_input.toPlainText().strip()
        if description:
            data['description'] = description
        
        location = self.location_input.text().strip()
        if location:
            data['location'] = location
        
        attendees_str = self.attendees_input.text().strip()
        if attendees_str:
            emails = [e.strip() for e in attendees_str.split(',') if e.strip()]
            data['attendees'] = emails
        
        return data