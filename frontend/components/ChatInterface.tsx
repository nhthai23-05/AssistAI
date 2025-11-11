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

import { useState } from 'react';

export function ChatInterface() {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    // Gọi backend qua IPC
    const response = await (window as any).api.sendMessage(input);
    
    setMessages(prev => [...prev, { role: 'assistant', content: response.reply }]);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>{msg.content}</div>
        ))}
      </div>
      <input 
        value={input} 
        onChange={e => setInput(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
