import { useState } from 'react';
import { TitleBar } from './components/TitleBar';
import { LeftSidebar } from './components/LeftSidebar';
import { ChatInterface } from './components/ChatInterface';
import { CalendarInterface } from './components/CalendarInterface';
import { SheetsInterface } from './components/SheetsInterface';
import { SettingsInterface } from './components/SettingsInterface';

type Service = 'chat' | 'calendar' | 'sheets' | 'add' | 'settings';

export default function App() {
  const [activeService, setActiveService] = useState<Service>('chat');
  const [darkMode, setDarkMode] = useState(false);

  const renderMainContent = () => {
    switch (activeService) {
      case 'chat':
        return <ChatInterface darkMode={darkMode} />;
      case 'calendar':
        return <CalendarInterface darkMode={darkMode} />;
      case 'sheets':
        return <SheetsInterface darkMode={darkMode} />;
      case 'settings':
        return <SettingsInterface darkMode={darkMode} onDarkModeToggle={() => setDarkMode(!darkMode)} />;
      case 'add':
        return (
          <div className="flex-1 flex items-center justify-center h-screen">
            <div className="text-center space-y-4">
              <div className={`text-6xl ${darkMode ? 'text-gray-700' : 'text-gray-300'}`}>+</div>
              <h3 className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
                Add New Service
              </h3>
              <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                Connect additional productivity tools here
              </p>
            </div>
          </div>
        );
      default:
        return <ChatInterface darkMode={darkMode} />;
    }
  };

  return (
    <div className={`flex flex-col h-screen ${darkMode ? 'bg-gray-950 text-white' : 'bg-white text-gray-900'}`}>
      <TitleBar darkMode={darkMode} />
      <div className="flex flex-1 overflow-hidden">
        <LeftSidebar
          activeService={activeService}
          onServiceChange={setActiveService}
          darkMode={darkMode}
        />
        {renderMainContent()}
      </div>
    </div>
  );
}
