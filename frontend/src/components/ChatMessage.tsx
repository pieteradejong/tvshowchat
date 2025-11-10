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
  snippet?: string;
  extraSnippets?: string[];
}

export function ChatMessage({
  message,
  isUser,
  timestamp,
  episodeInfo,
  snippet,
  extraSnippets,
}: ChatMessageProps) {
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
        {!isUser && snippet && (
          <div className="mt-3 rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3 text-sm text-gray-800 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Primary match</p>
            <p className="mt-2 whitespace-pre-line leading-relaxed">{snippet}</p>
          </div>
        )}
        {!isUser && extraSnippets && extraSnippets.length > 0 && (
          <div className="mt-3 space-y-2 text-sm text-gray-600">
            {extraSnippets.map((text, index) => (
              <div
                key={`extra-snippet-${index}`}
                className="rounded-md border border-gray-200 bg-white p-3 text-gray-700 shadow-sm"
              >
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Supporting snippet</p>
                <p className="mt-1 whitespace-pre-line leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        )}
        <time className={`mt-1 block text-xs ${isUser ? 'text-primary-100' : 'text-gray-400'}`}>
          {format(timestamp, 'h:mm a')}
        </time>
      </div>
    </div>
  );
} 