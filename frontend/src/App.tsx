// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import { ChatWindow } from './components/ChatWindow';
import Search from './components/Search';
import { UseCases } from './components/UseCases';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

type Tab = 'search' | 'chat' | 'useCases';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('search');
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);

  const handlePromptSelect = useCallback((prompt: string) => {
    setPendingPrompt(prompt);
    setActiveTab('search');
  }, []);

  const handlePromptConsumed = useCallback(() => {
    setPendingPrompt(null);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <div className="sm:hidden">
              <select
                value={activeTab}
                onChange={(e) => setActiveTab(e.target.value as Tab)}
                className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              >
                <option value="search">Search Episodes</option>
                <option value="chat">Chat</option>
                <option value="useCases">Use Cases</option>
              </select>
            </div>
            <div className="hidden sm:block">
              <nav className="flex space-x-4" aria-label="Tabs">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`${
                    activeTab === 'search'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-3 py-2 font-medium text-sm rounded-md`}
                >
                  Search Episodes
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`${
                    activeTab === 'chat'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-3 py-2 font-medium text-sm rounded-md`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab('useCases')}
                  className={`${
                    activeTab === 'useCases'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-3 py-2 font-medium text-sm rounded-md`}
                >
                  Use Cases
                </button>
              </nav>
            </div>
            <p className="mt-3 text-sm text-gray-500">
              Switch between semantic episode search, conversational chat, or curated use-case prompts.
            </p>
          </div>

          <div className="mt-6">
            {activeTab === 'search' && (
              <Search pendingPrompt={pendingPrompt ?? undefined} onPromptConsumed={handlePromptConsumed} />
            )}
            {activeTab === 'chat' && <ChatWindow />}
            {activeTab === 'useCases' && <UseCases onSelectPrompt={handlePromptSelect} />}
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}
