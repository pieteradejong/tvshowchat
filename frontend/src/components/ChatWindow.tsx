import { useState, useRef, useEffect } from 'react';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { PromptExamples } from './PromptExamples';

interface SearchApiResult {
  season: number;
  episode: string;
  title: string;
  airdate: string;
  text: string;
  snippets?: string[];
}

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
  snippet?: string;
  extraSnippets?: string[];
}

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const promptCategories = [
    {
      title: 'Mood-Based Watching',
      prompts: [
        'Comfort episodes after a tough day',
        'Need a spooky Buffy marathon tonight',
        'Lighthearted episodes with musical moments',
      ],
    },
    {
      title: 'Character Arcs',
      description: 'Ask for multi-episode lists that chart a character’s growth.',
      prompts: [
        'Series of episodes to watch for Willow’s magic arc',
        'Trace Buffy’s leadership journey across the series',
        'Spike’s redemption episodes in order',
      ],
    },
    {
      title: 'Themes',
      prompts: [
        'Episodes exploring grief and loss',
        'Stories about friendship saving the world',
        'Episodes tackling power and responsibility',
      ],
    },
  ];

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
      // Use relative URL - works in both dev (proxy) and production (same domain)
      const apiUrl = import.meta.env.VITE_API_URL || '/api/search';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: text }),
      });

      const data: SearchApiResult[] = await response.json();

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
          snippet: firstResult.text,
          extraSnippets: firstResult.snippets || [],
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

  const handlePromptSelect = (prompt: string) => {
    void handleSendMessage(prompt);
  };

  return (
    <div className="flex flex-col min-h-[400px] max-h-[calc(100vh-12rem)] sm:max-h-[calc(100vh-8rem)] bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <header className="bg-white border-b p-3 sm:p-4">
        <h1 className="text-lg sm:text-xl font-semibold text-gray-900">Buffy Chat</h1>
        <p className="text-xs sm:text-sm text-gray-500">Ask me anything about Buffy the Vampire Slayer</p>
      </header>

      <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
        {messages.length === 0 && (
          <PromptExamples
            heading="Not sure where to start?"
            categories={promptCategories}
            onSelectPrompt={handlePromptSelect}
          />
        )}
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
            episodeInfo={message.episodeInfo}
            snippet={message.snippet}
            extraSnippets={message.extraSnippets}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
} 