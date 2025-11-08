import { Minus, Square, X, Bot } from 'lucide-react';
import { Button } from './ui/button';

// Extend window interface for Electron API
declare global {
  interface Window {
    electronAPI?: {
      minimizeWindow: () => void;
      maximizeWindow: () => void;
      closeWindow: () => void;
      isMaximized: () => Promise<boolean>;
    };
  }
}

interface TitleBarProps {
  darkMode: boolean;
}

export function TitleBar({ darkMode }: TitleBarProps) {
  const handleMinimize = () => {
    if (window.electronAPI) {
      window.electronAPI.minimizeWindow();
    } else {
      console.log('Minimize window (web mode)');
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI) {
      window.electronAPI.maximizeWindow();
    } else {
      console.log('Maximize/Restore window (web mode)');
    }
  };

  const handleClose = () => {
    if (window.electronAPI) {
      window.electronAPI.closeWindow();
    } else {
      console.log('Close window (web mode)');
    }
  };

  return (
    <div
      className={`h-12 flex items-center justify-between px-4 border-b select-none ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-gray-50 border-gray-200'
      }`}
      style={{ WebkitAppRegion: 'drag' } as any}
    >
      {/* Left: App Logo/Name */}
      <div className="flex items-center gap-2">
        <div className={`p-1.5 rounded ${darkMode ? 'bg-blue-600' : 'bg-blue-500'}`}>
          <Bot className="w-4 h-4 text-white" />
        </div>
        <span className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
          AI Assistant
        </span>
      </div>

      {/* Middle: Drag Region (expandable) */}
      <div className="flex-1" />

      {/* Right: Window Controls */}
      <div className="flex items-center gap-1" style={{ WebkitAppRegion: 'no-drag' } as any}>
        <Button
          variant="ghost"
          size="icon"
          className={`h-8 w-8 rounded ${
            darkMode
              ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-200'
              : 'hover:bg-gray-200 text-gray-600 hover:text-gray-900'
          }`}
          onClick={handleMinimize}
        >
          <Minus className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className={`h-8 w-8 rounded ${
            darkMode
              ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-200'
              : 'hover:bg-gray-200 text-gray-600 hover:text-gray-900'
          }`}
          onClick={handleMaximize}
        >
          <Square className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className={`h-8 w-8 rounded hover:bg-red-600 hover:text-white ${
            darkMode ? 'text-gray-400' : 'text-gray-600'
          }`}
          onClick={handleClose}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
