import { useState, FormEvent } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export function ChatInput({ onSendMessage, isLoading = false }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t bg-white">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask about Buffy episodes..."
        className="input flex-1"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={!message.trim() || isLoading}
        className="btn btn-primary"
      >
        <PaperAirplaneIcon className="h-5 w-5" />
        <span className="sr-only">Send message</span>
      </button>
    </form>
  );
} 