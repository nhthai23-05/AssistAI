import { useState } from 'react';
import { Send, Loader2, Wrench } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import { Avatar } from './ui/avatar';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status?: 'thinking' | 'using-tool' | 'complete';
  toolName?: string;
}

interface ChatInterfaceProps {
  darkMode: boolean;
}

export function ChatInterface({ darkMode }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. I can help you manage your calendar, organize your sheets, and much more. What would you like to do today?',
      status: 'complete',
    },
    {
      id: '2',
      role: 'user',
      content: 'Can you check my calendar for tomorrow?',
      status: 'complete',
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Let me check your calendar...',
      status: 'using-tool',
      toolName: 'Checking your calendar',
    },
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      status: 'complete',
    };

    setMessages([...messages, newMessage]);
    setInput('');

    // Simulate AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '',
          status: 'thinking',
        },
      ]);
    }, 500);
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className={`px-6 py-4 border-b ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
      }`}>
        <h2 className={darkMode ? 'text-white' : 'text-gray-900'}>AI Assistant</h2>
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Your intelligent productivity companion
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="px-6 py-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <Avatar className={`w-8 h-8 flex items-center justify-center ${
                  darkMode ? 'bg-blue-600' : 'bg-blue-500'
                }`}>
                  <span className="text-white">AI</span>
                </Avatar>
              )}
              <div
                className={`max-w-[70%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? darkMode
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-500 text-white'
                    : darkMode
                    ? 'bg-gray-800 text-gray-100'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.status === 'thinking' && (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
                      Thinking...
                    </span>
                  </div>
                )}
                {message.status === 'using-tool' && (
                  <div className="flex items-center gap-2">
                    <Wrench className="w-4 h-4" />
                    <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
                      {message.toolName || 'Using tool...'}
                    </span>
                  </div>
                )}
                {message.status === 'complete' && message.content && (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
              {message.role === 'user' && (
                <Avatar className={`w-8 h-8 flex items-center justify-center ${
                  darkMode ? 'bg-gray-700' : 'bg-gray-300'
                }`}>
                  <span className={darkMode ? 'text-gray-200' : 'text-gray-700'}>U</span>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className={`px-6 py-4 border-t ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
      }`}>
        <div className="flex gap-2">
          <Textarea
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            className={`resize-none ${
              darkMode
                ? 'bg-gray-800 border-gray-700 text-white placeholder:text-gray-500'
                : 'bg-white border-gray-300 text-gray-900'
            }`}
            rows={3}
          />
          <Button
            onClick={handleSend}
            className={darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
