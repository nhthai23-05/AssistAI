"""Thread classes for async operations without blocking UI"""

from PyQt6.QtCore import QThread, pyqtSignal


class APIThread(QThread):
    """Generic thread for API calls"""
    success = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.success.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CalendarChatThread(QThread):
    """Thread để gọi calendar smart action API không block UI"""
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


class ChatThread(QThread):
    """Thread để gọi chat API không block UI"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, service, message, conversation_history=None):
        super().__init__()
        self.service = service
        self.message = message
        self.conversation_history = conversation_history or []
    
    def run(self):
        try:
            result = self.service.send_message(self.message, self.conversation_history)
            response = result.get('response', result.get('message', 'No response'))
            self.response_received.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))
