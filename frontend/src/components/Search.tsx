// Search.tsx
import { FC, useState } from 'react';
import axios from 'axios';

interface SearchResult {
  episode_number: string;
  episode_title: string;
  episode_airdate: string;
  episode_summary: string[];
  score: number;
}

const Search: FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:8000/api/search', { 
        query: searchQuery,
        top_k: 3 
      });
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setError('Failed to perform search. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search Buffy episodes..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          onClick={handleSearch}
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {searchResults.map((result) => (
          <div 
            key={`${result.episode_number}-${result.episode_title}`}
            className="p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold text-gray-900">
                {result.episode_number}. {result.episode_title}
              </h3>
              <span className="text-sm text-gray-500">
                Score: {Math.round(result.score * 100)}%
              </span>
            </div>
            <div className="prose prose-sm max-w-none">
              <div className="mb-2 text-sm text-gray-500">
                Aired: {new Date(result.episode_airdate).toLocaleDateString()}
              </div>
              <div className="space-y-2">
                {result.episode_summary.map((summary, index) => (
                  <p key={index} className="text-gray-600">{summary}</p>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {searchResults.length === 0 && !isLoading && !error && searchQuery && (
        <div className="text-center text-gray-500 mt-8">
          No episodes found matching your search.
        </div>
      )}
    </div>
  );
};

export default Search;

