from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path
import json

CONFIG_PATH = Path(__file__).parent.parent / "config"
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_oauth_url():
    """Tạo OAuth URL để user đăng nhập"""
    flow = Flow.from_client_secrets_file(
        str(CONFIG_PATH / 'credentials.json'),
        scopes=SCOPES,
        redirect_uri='http://localhost:8000/api/auth/callback'
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    # Lưu state để verify sau
    with open(CONFIG_PATH / 'oauth_state.json', 'w') as f:
        json.dump({'state': state}, f)
    
    return auth_url

def handle_oauth_callback(code: str):
    """Xử lý callback từ Google, lưu token"""
    flow = Flow.from_client_secrets_file(
        str(CONFIG_PATH / 'credentials.json'),
        scopes=SCOPES,
        redirect_uri='http://localhost:8000/api/auth/callback'
    )
    
    # Exchange code để lấy token
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Lưu token vào file
    save_credentials(credentials)
    
    return True

def save_credentials(credentials):
    """Lưu credentials vào file"""
    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open(CONFIG_PATH / 'token.json', 'w') as f:
        json.dump(token_data, f)

def has_valid_token():
    """
    EAGER VERIFICATION: Check token có tồn tại VÀ hợp lệ không
    Return True chỉ khi token:
    - Tồn tại
    - Không expired (hoặc có thể refresh)
    - Không bị revoke
    """
    token_file = CONFIG_PATH / 'token.json'
    
    # Bước 1: Check file tồn tại
    if not token_file.exists():
        return False
    
    try:
        # Bước 2: Load credentials từ file
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Bước 3: Check token có expired không
        if credentials.expired:
            # Nếu có refresh token → Thử refresh
            if credentials.refresh_token:
                try:
                    print("⏳ Token expired, refreshing...")
                    credentials.refresh(Request())
                    
                    # Refresh thành công → Lưu lại token mới
                    save_credentials(credentials)
                    print("✅ Token refreshed successfully")
                    return True
                    
                except Exception as refresh_error:
                    # Refresh failed → Token không còn hợp lệ
                    print(f"❌ Token refresh failed: {refresh_error}")
                    print("→ Token may be revoked or refresh_token expired")
                    return False
            else:
                # Không có refresh token → Không thể refresh
                print("❌ Token expired and no refresh_token available")
                return False
        
        # Bước 4: Token còn hợp lệ
        return True
        
    except Exception as e:
        # Lỗi khi load/parse token → Token không hợp lệ
        print(f"❌ Error checking token: {e}")
        return False

def get_credentials():
    """
    Load credentials từ token.json
    Với Eager Verification, has_valid_token() đã check rồi
    → Hàm này chỉ cần load thôi
    """
    if not has_valid_token():
        return None
    
    with open(CONFIG_PATH / 'token.json', 'r') as f:
        token_data = json.load(f)
    
    credentials = Credentials(
        token=token_data['token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data['scopes']
    )
    
    return credentials

def logout():
    """Xóa token"""
    token_file = CONFIG_PATH / 'token.json'
    if token_file.exists():
        token_file.unlink()
        print("✅ Token deleted")
    return True