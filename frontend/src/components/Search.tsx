// Search.tsx
import { FC, useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { DEFAULT_PROMPT_CATEGORIES } from './PromptExamples';
import { TimelineView } from './TimelineView';
import { SearchResult } from '../types/search';

interface SearchProps {
  pendingPrompt?: string;
  onPromptConsumed?: () => void;
}

const Search: FC<SearchProps> = ({ pendingPrompt, onPromptConsumed }) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');

  const allExamplePrompts = useMemo(
    () => DEFAULT_PROMPT_CATEGORIES.flatMap((category) => category.prompts),
    []
  );

  const pickSuggestions = useCallback(() => {
    if (allExamplePrompts.length <= 3) {
      return allExamplePrompts.slice();
    }

    const pool = [...allExamplePrompts];
    const selections: string[] = [];

    while (pool.length > 0 && selections.length < 3) {
      const index = Math.floor(Math.random() * pool.length);
      selections.push(pool.splice(index, 1)[0]);
    }

    return selections;
  }, [allExamplePrompts]);

  const [suggestions, setSuggestions] = useState<string[]>(() => pickSuggestions());

  const executeSearch = useCallback(
    async (query: string) => {
      if (!query.trim()) return;

      setIsLoading(true);
      setError(null);

      try {
        // Use relative URL - works in both dev (proxy) and production (same domain)
        const apiUrl = import.meta.env.VITE_API_URL || '/api/search';
        const response = await axios.post(apiUrl, {
          query,
          limit: 5,
        });
        setSearchResults(response.data || []);
      } catch (error) {
        console.error('Search error:', error);
        setError('Failed to perform search. Please try again.');
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    await executeSearch(searchQuery);
  };

  useEffect(() => {
    if (!pendingPrompt || !pendingPrompt.trim()) {
      return;
    }

    setSearchQuery(pendingPrompt);
    void executeSearch(pendingPrompt);
    onPromptConsumed?.();
  }, [pendingPrompt, executeSearch, onPromptConsumed]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-3 sm:p-4">
      <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 p-3 sm:p-4 text-sm text-blue-900">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
          <p className="font-medium text-blue-800">Try searches like:</p>
          <button
            type="button"
            onClick={() => setSuggestions(pickSuggestions())}
            className="self-start sm:self-auto rounded-md border border-blue-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-700 transition hover:border-blue-300 hover:text-blue-900"
          >
            Shuffle suggestions
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                setSearchQuery(suggestion);
                void executeSearch(suggestion);
              }}
              className="rounded-full border border-blue-200 bg-white px-3 sm:px-4 py-1 text-xs sm:text-sm font-medium text-blue-700 transition hover:border-blue-300 hover:bg-blue-100"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {searchResults.length > 0 && (
        <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
          <p className="text-xs sm:text-sm text-gray-600">
            {searchResults.length} {searchResults.length === 1 ? 'episode' : 'episodes'} found
          </p>
          <div className="inline-flex rounded-lg border border-blue-200 bg-white p-1 text-xs font-medium text-blue-700">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`rounded-md px-2 sm:px-3 py-1 transition ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-blue-700 hover:bg-blue-50'
              }`}
              aria-pressed={viewMode === 'list'}
            >
              List
            </button>
            <button
              type="button"
              onClick={() => setViewMode('timeline')}
              className={`rounded-md px-2 sm:px-3 py-1 transition ${
                viewMode === 'timeline'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-blue-700 hover:bg-blue-50'
              }`}
              aria-pressed={viewMode === 'timeline'}
            >
              Timeline
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-2 mb-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search Buffy episodes..."
          className="flex-1 px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="w-full sm:w-auto px-4 sm:px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-sm sm:text-base"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 sm:p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {viewMode === 'list' ? (
        <div className="space-y-3 sm:space-y-4">
          {searchResults.map((result) => (
            <div
              key={`${result.season}-${result.episode}-${result.title}`}
              className="p-3 sm:p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900">
                  S{String(result.season).padStart(2, '0')}E{result.episode}. {result.title}
                </h3>
                <span className="text-xs sm:text-sm text-gray-500">
                  Score: {Math.round(result.score * 100)}%
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span className="rounded bg-blue-50 px-2 py-1 uppercase tracking-wide text-blue-600">
                  {result.content_type}
                </span>
                {result.context && <span>{result.context}</span>}
              </div>
              <div className="prose prose-sm max-w-none">
                <div className="mb-2 text-xs sm:text-sm text-gray-500">Aired: {result.airdate}</div>

                {result.characters.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-blue-600">Characters: </span>
                    <span className="text-xs text-gray-600">{result.characters.join(', ')}</span>
                  </div>
                )}

                {result.themes.length > 0 && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-green-600">Themes: </span>
                    <span className="text-xs text-gray-600">{result.themes.join(', ')}</span>
                  </div>
                )}

                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3 sm:p-4 text-xs sm:text-sm text-gray-800 shadow-sm">
                    <p className="font-medium uppercase tracking-wide text-amber-700 text-xs mb-1">Primary match</p>
                    <p className="leading-relaxed whitespace-pre-line break-words">{result.text}</p>
                  </div>

                  {result.snippets && result.snippets.length > 0 && (
                    <div className="rounded-lg bg-gray-50 p-2 sm:p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                        Supporting snippets
                      </p>
                      <ul className="mt-2 space-y-2">
                        {result.snippets.map((snippet, index) => (
                          <li
                            key={`${result.title}-snippet-${index}`}
                            className="rounded-md border border-gray-200 bg-white p-2 sm:p-3 text-xs sm:text-sm text-gray-700 shadow-sm"
                          >
                            <span className="block whitespace-pre-line leading-relaxed break-words">{snippet}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <TimelineView results={searchResults} />
      )}

      {searchResults.length === 0 && !isLoading && !error && searchQuery && (
        <div className="text-center text-sm sm:text-base text-gray-500 mt-6 sm:mt-8">
          No episodes found matching your search.
        </div>
      )}
    </div>
  );
};

export default Search;

