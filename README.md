# AssistAI Desktop

Ứng dụng desktop AI assistant được xây dựng bằng Electron + Vite + React, tích hợp với Google Calendar, Google Sheets và AI chatbot.

---

## 🎯 Tổng quan dự án

AssistAI là ứng dụng desktop giúp người dùng:
- Chat với AI assistant
- Quản lý Google Calendar
- Tương tác với Google Sheets
- Cấu hình settings và authentication

**Stack công nghệ:**
- **Frontend:** React 18 + TypeScript + Vite + Electron + Radix UI + Tailwind CSS
- **Backend:** FastAPI (Python) + Google APIs (Calendar, Sheets)
- **AI:** OpenAI API

---

## 📁 Cấu trúc thư mục

```
AssistAI/
├── frontend/                 # Electron + React app
│   ├── electron/
│   │   ├── main.js          # Electron main process
│   │   └── preload.js       # IPC bridge
│   ├── components/          # React components
│   │   ├── ChatInterface.tsx
│   │   ├── CalendarInterface.tsx
│   │   ├── SheetsInterface.tsx
│   │   ├── SettingsInterface.tsx
│   │   └── ui/              # shadcn/ui components
│   ├── App.tsx
│   ├── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                 # FastAPI server
    ├── config/
    │   ├── credentials.json # Google OAuth credentials
    │   ├── token.json       # OAuth token (auto-generated)
    │   └── settings.json    # App settings
    ├── config_example/      # Template configs
    ├── server.py            # Main FastAPI app (TẠO MỚI)
    ├── services/            # Business logic (TẠO MỚI)
    │   ├── ai_service.py
    │   ├── calendar_service.py
    │   └── sheets_service.py
    └── requirements.txt
```

---

## 🛠 Yêu cầu hệ thống

- **Node.js:** >= 18.x
- **Python:** >= 3.9
- **npm** hoặc **yarn**
- **pip**

---

### **PHASE 3: Hoàn thiện features** (⭐)

- [ ] Implement Calendar CRUD (create/update/delete events)
- [ ] Implement Sheets read/write
- [ ] Add authentication UI trong Settings
- [ ] Lưu chat history vào local storage
- [ ] Thêm error handling và loading states
- [ ] Styling với Tailwind + shadcn/ui

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Chat với AI |
| `GET` | `/api/calendar/events` | Lấy danh sách events |
| `POST` | `/api/calendar/events` | Tạo event mới |
| `GET` | `/api/sheets/{sheetId}` | Đọc data từ sheet |
| `POST` | `/api/sheets/{sheetId}` | Ghi data vào sheet |

---

## 🏃 Chạy ứng dụng

### Development mode

**Terminal 1 (Backend):**
```bash
cd backend
python server.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Build production

```bash
cd frontend
npm run build
```
