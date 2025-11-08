# AssistAI Desktop Application

A modern AI Assistant desktop application built with Electron, React, TypeScript, and Vite.

## Features

- 🖥️ **Desktop Application**: Native Windows, macOS, and Linux support
- 🎨 **Modern UI**: Beautiful interface with Radix UI components
- 🌓 **Dark Mode**: Full dark/light theme support
- 💬 **Chat Interface**: AI-powered conversation interface
- 📅 **Calendar**: Integrated calendar management
- 📊 **Sheets**: Spreadsheet functionality
- ⚙️ **Settings**: Customizable application settings
- 🪟 **Custom Title Bar**: Frameless window with custom controls

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Development Mode

Run the application in development mode with hot-reload:

```bash
npm run electron:dev
```

This will:
- Start Vite dev server on `http://localhost:5173`
- Wait for server to be ready
- Launch Electron application

### 3. Build for Production

Build the application for your platform:

**Windows:**
```bash
npm run electron:build:win
```

**macOS:**
```bash
npm run electron:build:mac
```

**Linux:**
```bash
npm run electron:build:linux
```

**All platforms:**
```bash
npm run electron:build
```

Built applications will be in the `dist-electron` folder.

## Available Scripts

- `npm run dev` - Start Vite dev server only (web mode)
- `npm run build` - Build React app for production
- `npm run electron:dev` - Run in Electron development mode
- `npm run electron:build` - Build for all platforms
- `npm run electron:build:win` - Build for Windows
- `npm run electron:build:mac` - Build for macOS
- `npm run electron:build:linux` - Build for Linux

## Technologies Used

- **Electron** - Desktop application framework
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Radix UI** - Headless UI components
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library

## IPC Communication

The application uses Electron's IPC (Inter-Process Communication) for window controls:

- `window-minimize` - Minimize the window
- `window-maximize` - Maximize/restore the window
- `window-close` - Close the window
- `window-is-maximized` - Check if window is maximized

## Customization

### Window Size

Edit `electron/main.js` to change default window dimensions:

```javascript
mainWindow = new BrowserWindow({
  width: 1400,    // Default width
  height: 900,    // Default height
  minWidth: 1000, // Minimum width
  minHeight: 600, // Minimum height
  // ...
});
```

### App Icons

Place your application icons in the `build/` folder:
- `build/icon.ico` - Windows icon
- `build/icon.icns` - macOS icon
- `build/icon.png` - Linux icon

### App ID and Name

Edit `package.json` build configuration:

```json
"build": {
  "appId": "com.assistai.desktop",
  "productName": "AssistAI",
  // ...
}
```

