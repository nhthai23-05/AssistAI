# AssistAI Desktop Assistant
Ứng dụng trợ lý AI tích hợp quản lý lịch làm việc và bảng thu chi cá nhân với Google Sheet và Google Calendar.
Hiện tại dự án đang trong giai đoạn hoàn thành và kiểm tra lại Frontend, sau đó sẽ tiếp tục với Backend
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
- Modern UI với Tailwind + shadcn/ui


## 7. Các vấn đề cần giải quyết
### 7.1. Vấn đề Backend

#### IPC Communication
- Đồng bộ dữ liệu giữa Electron main process và renderer process
- Đảm bảo type-safe cho các IPC calls
- Xử lý errors và timeout cho IPC communication

#### OAuth Flow
- Quản lý token lifecycle (refresh, expire) --> Hiện tại đang giải quyết bằng việc để Project là Production trên GG Cloud Console
- Lưu trữ credentials an toàn trong local storage

#### State Management
- Quản lý state giữa các modules
- Đồng bộ state giữa UI và backend

#### Error Handling
- Thông báo lỗi khi người dùng tương tác sai
- Logging errors

#### Data Persistence
- Lưu trữ chat history trong local storage
- Sync data giữa local và cloud
- Data migration và backup strategy

### 7.2. Vấn đề Frontend
#### Loading States
- Hiển thị progress cho các task
- Skeleton screens cho data fetching
- Optimistic UI updates

#### Offline Mode (đang cân nhắc)
- Xử lý khi mất kết nối internet
- Cache data để sử dụng offline
- Sync khi reconnect

#### Navigation
- Chuyển đổi mượt giữa các modules
- Breadcrumb navigation

#### Notifications
- Thông báo không làm gián đoạn workflow
- Priority levels cho notifications

## 8. Dự kiến hướng giải quyết
### 8.1. Frontend Architecture

#### Công nghệ sử dụng
- **Framework**: Electron với React
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React Context API
- **IPC**: Type-safe preload bridge

#### Giải thích lý do lựa chọn
- **Framework**:
- Dễ mở rộng ra các hệ điều hành khác. Bắt đầu với Windows và mở rộng ra MacOS và Linux dễ dàng hơn
- React có nhiều thư viện để triển khai dự án, triển khai thành Desktop App dễ hơn

- **Build tool**:
- Tốc độ build và reload nhanh
- Hỗ trợ Electron và React tốt nhất

- **Styling**:
- shadcn/ui có design đa dạng, dễ triển khai, nhiều components. Phù hợp nhất cho UI development với người mới bắt đầu
- Tailwind có performance tốt, không cần runtime

- **State Management**:
- Giải thích về State Management: Nó là 1 thành phần của dự án, nó là cách quản lý dữ liệu và trạng thái của ứng dụng.
- React Context API dễ hiểu, dễ học, chỉ có 4-5 modules nên dễ cho người mới bắt đầu

- **IPC**:
- IPC (Inter-Process Communication) chính là cách mà 2 phần của Electron app nói chuyện với nhau:
  - Phần giao diện: Renderer Process
  - Phần hệ thống: Main Process

### 8.2. Backend Architecture

#### Công nghệ sử dụng
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Authentication**: Google OAuth 2.0
- **APIs**: OpenAI, Google Calendar, Google Sheets
- **Storage**: Local file system + in-memory cache

#### Service Layer Design
- **AI Service**: Quản lý kết nối với OpenAI API, xử lý chat và lưu trữ lịch sử hội thoại
- **Calendar Service**: Tương tác với Google Calendar API, xử lý CRUD operations cho events
- **Sheet Service**: Tương tác với Google Sheets API, xử lý đọc/ghi dữ liệu

### 8.3. Data Flow

```
User Input → React Component → IPC Call → FastAPI Endpoint → Service Layer → External API → Response Processing → React State Update → UI Render
```

### 8.4. Authentication Flow (dự kiến giải quyết sau khi hoàn thành Frontend)

```
1. Người dùng kết nối với Google (cần tạo 1 nút ấn)
2. Frontend → Backend: Request OAuth URL
3. Backend xử lý tạo OAuth URL
4. Frontend mở browser với OAuth URL
5. Người dùng chấp nhận app
6. Google redirects tới local server
7. Backend exchanges code for tokens
8. Backend lưu tokens
9. Frontend nhận thông báo thành công và hiển thị
10. Hết flow authentication
```

### 8.5. Công nghệ dự kiến

#### Credentials Storage
- Mã hóa credentials sử dụng Fernet (cần đọc thêm về Fernet)
- Lưu trữ tokens trong file encrypted 

#### IPC Security
- Context isolation trong Electron
- Whitelist các IPC channels được phép
- Kiểm tra input data 

## 9. API Documentation (dự kiến)

### 9.1. AI Chat Endpoints

**POST /api/chat**
- **Request**: message (string), context (array)
- **Response**: response (string), timestamp (ISO datetime)
- **Chức năng**: Gửi message đến AI và nhận phản hồi

### 9.2. Calendar Endpoints

**GET /api/calendar/events**
- **Query params**: time_min, time_max (ISO datetime)
- **Response**: Danh sách events với id, summary, start, end
- **Chức năng**: Lấy danh sách sự kiện trong khoảng thời gian

**POST /api/calendar/events**
- **Request**: summary, description, start, end
- **Response**: Event được tạo với id
- **Chức năng**: Tạo sự kiện mới trong calendar

**PUT /api/calendar/events/{id}** - Cập nhật sự kiện

**DELETE /api/calendar/events/{id}** - Xóa sự kiện

### 9.3. Sheets Endpoints

**GET /api/sheets/data**
- **Query params**: sheet_id, range (ví dụ: "Sheet1!A1:D10")
- **Response**: values (array 2D)
- **Chức năng**: Đọc dữ liệu từ Google Sheet

**POST /api/sheets/data**
- **Request**: sheet_id, range, values
- **Response**: Số rows được ghi
- **Chức năng**: Ghi dữ liệu vào Google Sheet

**GET /api/sheets/search** - Tìm kiếm trong sheet