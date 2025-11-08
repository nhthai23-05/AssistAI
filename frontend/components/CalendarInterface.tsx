import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  color: string;
}

interface CalendarInterfaceProps {
  darkMode: boolean;
}

export function CalendarInterface({ darkMode }: CalendarInterfaceProps) {
  const [view, setView] = useState<'day' | 'week' | 'month'>('week');
  const [currentDate, setCurrentDate] = useState(new Date());

  // Mock events
  const events: CalendarEvent[] = [
    {
      id: '1',
      title: 'Team Standup',
      start: new Date(2025, 10, 10, 9, 0),
      end: new Date(2025, 10, 10, 9, 30),
      color: 'bg-blue-500',
    },
    {
      id: '2',
      title: 'Project Review',
      start: new Date(2025, 10, 10, 14, 0),
      end: new Date(2025, 10, 10, 15, 30),
      color: 'bg-purple-500',
    },
    {
      id: '3',
      title: 'Client Meeting',
      start: new Date(2025, 10, 11, 10, 0),
      end: new Date(2025, 10, 11, 11, 0),
      color: 'bg-green-500',
    },
    {
      id: '4',
      title: 'Design Workshop',
      start: new Date(2025, 10, 12, 13, 0),
      end: new Date(2025, 10, 12, 16, 0),
      color: 'bg-orange-500',
    },
  ];

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const weekDates = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(2025, 10, 10 + i);
    return date;
  });

  const formatTime = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour} ${period}`;
  };

  const getEventPosition = (event: CalendarEvent, dayIndex: number) => {
    const eventDay = event.start.getDate();
    const currentDay = weekDates[dayIndex].getDate();
    
    if (eventDay !== currentDay) return null;

    const startHour = event.start.getHours();
    const startMinute = event.start.getMinutes();
    const endHour = event.end.getHours();
    const endMinute = event.end.getMinutes();

    const top = (startHour + startMinute / 60) * 60;
    const height = ((endHour + endMinute / 60) - (startHour + startMinute / 60)) * 60;

    return { top, height };
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className={`px-6 py-4 border-b ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h2 className={darkMode ? 'text-white' : 'text-gray-900'}>Calendar</h2>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className={darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className={`px-3 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                November 10-16, 2025
              </span>
              <Button
                variant="ghost"
                size="icon"
                className={darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <Tabs value={view} onValueChange={(v) => setView(v as any)}>
            <TabsList className={darkMode ? 'bg-gray-800' : 'bg-gray-100'}>
              <TabsTrigger value="day">Day</TabsTrigger>
              <TabsTrigger value="week">Week</TabsTrigger>
              <TabsTrigger value="month">Month</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      <div className={`flex-1 overflow-auto ${darkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className="min-w-[800px]">
          {/* Week view header */}
          <div className={`grid grid-cols-8 border-b sticky top-0 z-10 ${
            darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
          }`}>
            <div className="w-16"></div>
            {weekDates.map((date, i) => (
              <div
                key={i}
                className={`py-3 text-center border-l ${
                  darkMode ? 'border-gray-800' : 'border-gray-200'
                }`}
              >
                <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {weekDays[i]}
                </div>
                <div className={`mt-1 ${
                  date.getDate() === 10
                    ? darkMode
                      ? 'text-blue-400'
                      : 'text-blue-600'
                    : darkMode
                    ? 'text-gray-200'
                    : 'text-gray-900'
                }`}>
                  {date.getDate()}
                </div>
              </div>
            ))}
          </div>

          {/* Week view grid */}
          <div className="relative">
            {hours.map((hour) => (
              <div
                key={hour}
                className={`grid grid-cols-8 border-b ${
                  darkMode ? 'border-gray-800' : 'border-gray-200'
                }`}
                style={{ height: '60px' }}
              >
                <div className={`w-16 pr-2 text-right text-xs pt-1 ${
                  darkMode ? 'text-gray-500' : 'text-gray-500'
                }`}>
                  {hour > 0 && formatTime(hour)}
                </div>
                {weekDates.map((_, dayIndex) => (
                  <div
                    key={dayIndex}
                    className={`border-l relative ${
                      darkMode ? 'border-gray-800' : 'border-gray-200'
                    }`}
                  >
                    {events.map((event) => {
                      const position = getEventPosition(event, dayIndex);
                      if (!position) return null;

                      return (
                        <div
                          key={event.id}
                          className={`absolute left-1 right-1 ${event.color} text-white text-xs p-1 rounded overflow-hidden`}
                          style={{
                            top: `${position.top}px`,
                            height: `${position.height}px`,
                          }}
                        >
                          <div>{event.title}</div>
                          <div className="opacity-80">
                            {event.start.getHours()}:{event.start.getMinutes().toString().padStart(2, '0')}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
