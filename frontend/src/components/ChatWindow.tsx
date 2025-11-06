import { useState, useRef, useEffect } from 'react';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  episodeInfo?: {
    title: string;
    season: string;
    episode: string;
    airdate: string;
  };
}

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: text }),
      });

      const data = await response.json();

      // Backend returns array of results
      if (Array.isArray(data) && data.length > 0) {
        const firstResult = data[0];
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `Found ${data.length} episode(s). Top result: ${firstResult.title} (S${String(firstResult.season).padStart(2, '0')}E${firstResult.episode})`,
          isUser: false,
          timestamp: new Date(),
          episodeInfo: {
            title: firstResult.title,
            season: String(firstResult.season),
            episode: firstResult.episode,
            airdate: firstResult.airdate,
          },
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: 'No episodes found matching your search.',
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b p-4">
        <h1 className="text-xl font-semibold text-gray-900">Buffy Chat</h1>
        <p className="text-sm text-gray-500">Ask me anything about Buffy the Vampire Slayer</p>
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
            episodeInfo={message.episodeInfo}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
} 