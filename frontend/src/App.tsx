// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import Search from './components/Search';
import { Explore } from './components/Explore';
import { SeriesVis } from './components/SeriesVis';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

type Tab = 'search' | 'explore' | 'series';

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
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-4 sm:py-6 lg:py-8">
          <div className="mb-4 sm:mb-6 lg:mb-8">
            <div className="sm:hidden">
              <select
                value={activeTab}
                onChange={(e) => setActiveTab(e.target.value as Tab)}
                className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              >
                <option value="search">Search</option>
                <option value="explore">Explore</option>
                <option value="series">Series</option>
              </select>
            </div>
            <div className="hidden sm:block">
              <nav className="flex space-x-2 sm:space-x-4" aria-label="Tabs">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`${
                    activeTab === 'search'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-2 sm:px-3 py-2 font-medium text-xs sm:text-sm rounded-md`}
                >
                  Search
                </button>
                <button
                  onClick={() => setActiveTab('explore')}
                  className={`${
                    activeTab === 'explore'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-2 sm:px-3 py-2 font-medium text-xs sm:text-sm rounded-md`}
                >
                  Explore
                </button>
                <button
                  onClick={() => setActiveTab('series')}
                  className={`${
                    activeTab === 'series'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  } px-2 sm:px-3 py-2 font-medium text-xs sm:text-sm rounded-md`}
                >
                  Series
                </button>
              </nav>
            </div>
            <p className="mt-2 sm:mt-3 text-xs sm:text-sm text-gray-500">
              {activeTab === 'search' 
                ? 'Search directly when you know what you want.'
                : activeTab === 'explore'
                ? 'Explore sample queries and get inspired.'
                : 'Browse the series timeline, character arcs, and details.'}
            </p>
          </div>

          <div className="mt-4 sm:mt-6">
            {activeTab === 'search' && (
              <Search 
                pendingPrompt={pendingPrompt ?? undefined} 
                onPromptConsumed={handlePromptConsumed}
                onSwitchToExplore={() => setActiveTab('explore')}
              />
            )}
            {activeTab === 'explore' && <Explore onSelectPrompt={handlePromptSelect} />}
            {activeTab === 'series' && <SeriesVis />}
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}
