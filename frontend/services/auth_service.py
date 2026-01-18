import requests
from config import API

class AuthService:
    """Service để xử lý authentication"""
    
    def check_status(self):
        """Kiểm tra auth status"""
        response = requests.get(API.AUTH_STATUS)
        response.raise_for_status()
        return response.json()
    
    def logout(self):
        """Logout user"""
        response = requests.post(API.AUTH_LOGOUT)
        response.raise_for_status()
        return response.json()