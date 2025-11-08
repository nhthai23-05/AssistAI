import { MessageSquare, Calendar, Sheet, Plus, Settings } from 'lucide-react';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';

type Service = 'chat' | 'calendar' | 'sheets' | 'add' | 'settings';

interface LeftSidebarProps {
  activeService: Service;
  onServiceChange: (service: Service) => void;
  darkMode: boolean;
}

export function LeftSidebar({ activeService, onServiceChange, darkMode }: LeftSidebarProps) {
  const services = [
    { id: 'chat' as Service, icon: MessageSquare, label: 'Chat' },
    { id: 'calendar' as Service, icon: Calendar, label: 'Calendar' },
    { id: 'sheets' as Service, icon: Sheet, label: 'Sheets' },
    { id: 'add' as Service, icon: Plus, label: 'Add App' },
  ];

  return (
    <div className={`w-16 h-full flex flex-col items-center py-4 border-r ${
      darkMode ? 'bg-gray-900 border-gray-800' : 'bg-gray-50 border-gray-200'
    }`}>
      <TooltipProvider>
        <div className="flex-1 flex flex-col gap-2">
          {services.map((service) => (
            <Tooltip key={service.id}>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={`w-12 h-12 relative ${
                    activeService === service.id
                      ? darkMode
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                      : darkMode
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
                  }`}
                  onClick={() => onServiceChange(service.id)}
                >
                  <service.icon className="w-5 h-5" />
                  {activeService === service.id && (
                    <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r ${
                      darkMode ? 'bg-blue-400' : 'bg-blue-600'
                    }`} />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>{service.label}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className={`w-12 h-12 relative ${
                activeService === 'settings'
                  ? darkMode
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                  : darkMode
                  ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
              }`}
              onClick={() => onServiceChange('settings')}
            >
              <Settings className="w-5 h-5" />
              {activeService === 'settings' && (
                <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r ${
                  darkMode ? 'bg-blue-400' : 'bg-blue-600'
                }`} />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Settings</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
