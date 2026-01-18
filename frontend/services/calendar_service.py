import requests
from config import API

class CalendarService:
    """Service để xử lý calendar operations"""
    
    def list_events(self, max_results=20):
        """Lấy danh sách events"""
        response = requests.get(
            API.CALENDAR_EVENTS,
            params={'max_results': max_results}
        )
        response.raise_for_status()
        return response.json()
    
    def create_event(self, event_data):
        """Tạo event mới (manual)"""
        response = requests.post(API.CALENDAR_EVENTS, json=event_data)
        response.raise_for_status()
        return response.json()
    
    def update_event(self, event_data):
        """Update event"""
        event_id = event_data.pop('event_id')
        response = requests.put(
            f"{API.CALENDAR_EVENTS}/{event_id}",
            json=event_data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_event(self, event_id):
        """Xóa event"""
        response = requests.delete(f"{API.CALENDAR_EVENTS}/{event_id}")
        response.raise_for_status()
        return response.json()
    
    def smart_action(self, user_request):
        """Xử lý calendar action tự động - LLM tự detect action"""
        response = requests.post(
            f"{API.CALENDAR_EVENTS}/smart-action",
            json={'user_request': user_request}
        )
        response.raise_for_status()
        return response.json()
    
    def smart_create_event(self, user_request):
        """Tạo event bằng natural language"""
        response = requests.post(
            API.CALENDAR_SMART_CREATE,
            json={'user_request': user_request}
        )
        response.raise_for_status()
        return response.json()
    
    def smart_update_event(self, user_request):
        """Update event bằng natural language"""
        response = requests.put(
            API.CALENDAR_SMART_UPDATE,
            json={'user_request': user_request}
        )
        response.raise_for_status()
        return response.json()
    
    def smart_delete_event(self, user_request):
        """Xóa event bằng natural language"""
        response = requests.delete(
            API.CALENDAR_SMART_DELETE,
            json={'user_request': user_request}
        )
        response.raise_for_status()
        return response.json()