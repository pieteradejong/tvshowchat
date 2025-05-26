// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatWindow } from './components/ChatWindow';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <ChatWindow />
      </div>
    </QueryClientProvider>
  );
}
