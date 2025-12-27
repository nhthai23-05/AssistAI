# AssistAI Desktop Assistant
Ứng dụng trợ lý AI tích hợp quản lý lịch làm việc và bảng thu chi cá nhân với Google Sheet và Google Calendar.
Hiện tại dự án đang xây dựng Backend trước, sau đó sẽ phát triển Frontend với Flet
## 1. Tên đề tài

**AssistAI Desktop**

## 2. Mục tiêu
Xây dựng ứng dụng desktop AI assistant đa chức năng giúp người dùng:

- Tương tác với AI thông qua giao diện chat bot desktop
- Quản lý lịch làm việc tự động qua Google Calendar
- Thu thập và cập nhật bảng thu chi cá nhân từ Google Sheets
- Tự động hóa các tác vụ hàng ngày thông qua AI

## 3. Input/Output
### 3.1. User → System

**Thao tác trực tiếp:**
- **Chat messages**: Câu hỏi, yêu cầu dạng text gửi đến AI
- **Calendar operations**: Tạo/sửa/xóa sự kiện (tiêu đề, thời gian, mô tả, người tham gia)
- **Sheets operations**: Nhập, chỉnh sửa, tìm kiếm dữ liệu trong bảng tính
- **Settings configuration**: Cấu hình API keys, OAuth credentials, preferences

**Quyền truy cập:**
- Cấp quyền OAuth 2.0 cho Google Calendar và Sheets
- Xác thực OpenAI API key

### 3.2. System → User
- **Calendar display**: 
  - Danh sách sự kiện theo ngày/tuần/tháng
  - Thông báo nhắc nhở sự kiện sắp diễn ra
- **Sheets visualization**: 
  - Dữ liệu bảng tính được format và phân trang
  - Kết quả tìm kiếm và filter
- **System notifications**: 
  - Thông báo thành công/lỗi cho các thao tác
  - Cảnh báo mất kết nối

**Dữ liệu lưu trữ (Persistent):**
- **Lịch sử chat**: Lưu trữ lịch sử hội thoại trong local storage
- **Tương tác người dùng**: Theme, notification, calendar
- **Logs**: Error logs và activity logs để debug

## 5. Yêu cầu hệ thống
### AI Chat Module
- Tích hợp OpenAI API (GPT-5-nano)
- Lưu và hiển thị lịch sử chat
- Hỗ trợ streaming responses
- Context awareness (nhớ các câu hỏi trước)

### Calendar Module
- Create, Read, Update, Delete (CRUD operations) cho events
- Sync real-time với Google Calendar
- Hiển thị lịch dạng grid/list view
- Thông báo nhắc nhở

### Sheets Module
- Đọc/ghi dữ liệu từ Google Sheets
- Hiển thị dạng bảng với pagination
- Search và filter data
- Export/import data

## 6. Phạm vi dự án
- Desktop application cho Windows
- Tích hợp OpenAI, Google Calendar, Google Sheets
- Modern UI với Flet framework


## 7. Các vấn đề cần giải quyết
### 7.1. Vấn đề Backend

#### API Design
- Thiết kế RESTful API rõ ràng, dễ sử dụng
- Đảm bảo consistency trong response format
- Xử lý errors và status codes đúng chuẩn

#### OAuth Flow
- Quản lý token lifecycle (refresh, expire) --> Hiện tại đang giải quyết bằng việc để Project là Production trên GG Cloud Console
- Lưu trữ credentials an toàn trong local storage

#### State Management
- Quản lý session và user state
- Cache dữ liệu để tối ưu performance

#### Error Handling
- Xử lý và trả về lỗi có ý nghĩa cho Frontend
- Logging errors để debug

#### Data Persistence
- Lưu trữ chat history trong local storage
- Sync data giữa local và cloud
- Data migration và backup strategy

### 7.2. Vấn đề Frontend
#### UI/UX Design
- Thiết kế giao diện đơn giản, dễ sử dụng
- Responsive layout cho các kích thước màn hình khác nhau
- Consistent design language

#### Loading States
- Hiển thị progress cho các task
- Loading indicators cho API calls
- Optimistic UI updates

#### Navigation
- Chuyển đổi mượt giữa các modules
- Navigation menu rõ ràng

#### Notifications
- Thông báo không làm gián đoạn workflow
- Priority levels cho notifications

## 8. Dự kiến hướng giải quyết

### 8.1. Workflow phát triển
**Phase 1: Backend Development (Hiện tại)**
1. Xây dựng FastAPI server với các endpoints cơ bản
2. Tích hợp Google OAuth 2.0 cho Calendar và Sheets
3. Tích hợp OpenAI API
4. Implement các Service layers (AI, Calendar, Sheets)
5. Testing các endpoints với Postman/Thunder Client
6. Hoàn thiện error handling và logging

**Phase 2: Frontend Development (Sau này)**
1. Thiết kế UI layout với Flet
2. Kết nối Frontend với Backend qua HTTP requests
3. Implement các modules chính (Chat, Calendar, Sheets)
4. Xử lý state management và navigation
5. Testing và debugging
6. Package thành desktop app

### 8.2. Backend Architecture

#### Công nghệ sử dụng
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Server**: Uvicorn
- **Authentication**: Google OAuth 2.0
- **APIs**: OpenAI, Google Calendar, Google Sheets
- **Storage**: Local file system + in-memory cache

#### Service Layer Design
- **AI Service**: Quản lý kết nối với OpenAI API, xử lý chat và lưu trữ lịch sử hội thoại
- **Calendar Service**: Tương tác với Google Calendar API, xử lý CRUD operations cho events
- **Sheet Service**: Tương tác với Google Sheets API, xử lý đọc/ghi dữ liệu

### 8.3. Frontend Architecture (Dự kiến)

#### Công nghệ sử dụng
- **Framework**: Flet
- **Language**: Python 3.11+
- **Communication**: HTTP requests đến FastAPI backend
- **State Management**: Flet's built-in state management

#### Giải thích lý do lựa chọn Flet
- **Single Language**: Sử dụng Python cho cả Frontend và Backend, giảm context switching
- **Easy Learning Curve**: Cú pháp đơn giản, dễ học cho người mới bắt đầu
- **Cross-platform**: Hỗ trợ Windows, macOS, Linux từ cùng một codebase
- **Modern UI**: Built-in Material Design components, không cần CSS
- **Fast Development**: Rapid prototyping với hot reload
- **Native Performance**: Compile thành native app với Flutter engine

#### Module Structure
- **Chat Module**: Giao diện chat với AI, hiển thị history
- **Calendar Module**: View và quản lý events (grid/list view)
- **Sheets Module**: Hiển thị và chỉnh sửa dữ liệu dạng bảng
- **Settings Module**: Cấu hình API keys, preferences

### 8.4. Data Flow

```
User Input → Flet Component → HTTP Request → FastAPI Endpoint → Service Layer → External API → Response Processing → Flet State Update → UI Render
```

### 8.5. Authentication Flow

```
1. Người dùng click nút "Connect to Google" trong Settings
2. Frontend gửi request đến Backend: GET /api/auth/google/url
3. Backend tạo OAuth URL và trả về
4. Frontend mở browser với OAuth URL
5. Người dùng đăng nhập và chấp nhận quyền truy cập
6. Google redirects về local server của Backend
7. Backend nhận authorization code và exchange lấy tokens
8. Backend lưu tokens vào encrypted file
9. Backend trả về success response
10. Frontend hiển thị thông báo "Connected successfully"
```

### 8.6. Security

#### Credentials Storage
- Mã hóa credentials sử dụng Fernet (cryptography library)
- Lưu trữ tokens trong file encrypted trong local storage

#### API Security
- CORS configuration cho local development
- Input validation cho tất cả endpoints
- Rate limiting để tránh abuse

## 9. Thực nghiệm

### 9.1. Từ Electron + Vite sang Flet

Ban đầu, dự án được bắt đầu với **Electron + Vite + React + TypeScript** để xây dựng desktop app. Tuy nhiên, trong quá trình phát triển, đã gặp một số khó khăn:

**Vấn đề gặp phải:**
- **Ngôn ngữ**: Chưa thông thạo TypeScript và JavaScript, dẫn đến việc implement các tính năng chậm và hay gặp lỗi
- **Độ phức tạp**: Phải quản lý quá nhiều công nghệ khác nhau (TypeScript, React, Electron IPC, Node.js)
- **Hiệu suất phát triển**: Thời gian build và debug lâu, hot reload không ổn định
- **Learning curve**: Phải học nhiều thứ cùng lúc (React hooks, TypeScript types, Electron architecture)

**Quyết định chuyển sang Flet:**
- **Single language**: Chỉ cần Python cho cả Frontend và Backend, tận dụng kiến thức đã có
- **Đơn giản hơn**: Ít công nghệ cần học, syntax gần gũi và dễ hiểu
- **Phát triển nhanh hơn**: Hot reload nhanh, ít config, dễ debug
- **Hiệu suất tốt**: Build trên Flutter engine, performance native app
- **Phù hợp với dự án**: Là người làm một mình, cần optimize thời gian phát triển

**Kết luận**: Quyết định chuyển sang Flet giúp dự án tiến triển nhanh hơn và giảm độ phức tạp không cần thiết.