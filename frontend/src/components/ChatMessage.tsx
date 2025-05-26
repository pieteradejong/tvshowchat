import { format } from 'date-fns';

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp: Date;
  episodeInfo?: {
    title: string;
    season: string;
    episode: string;
    airdate: string;
  };
}

export function ChatMessage({ message, isUser, timestamp, episodeInfo }: ChatMessageProps) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-primary-600 text-white' : 'bg-white border'
        }`}
      >
        <p className="text-sm">{message}</p>
        {episodeInfo && (
          <div className={`mt-2 text-xs ${isUser ? 'text-primary-100' : 'text-gray-500'}`}>
            <p className="font-medium">{episodeInfo.title}</p>
            <p>Season {episodeInfo.season}, Episode {episodeInfo.episode}</p>
            <p>Aired: {format(new Date(episodeInfo.airdate), 'MMM d, yyyy')}</p>
          </div>
        )}
        <time className={`mt-1 block text-xs ${isUser ? 'text-primary-100' : 'text-gray-400'}`}>
          {format(timestamp, 'h:mm a')}
        </time>
      </div>
    </div>
  );
} 