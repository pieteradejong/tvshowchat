import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchQuotes, Quote } from "../../services/reminiscence";

const MAIN_CHARACTERS = [
  "Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia",
  "Oz", "Anya", "Faith", "Dawn", "Tara", "Riley", "Joyce",
];

export const QuoteExplorer: React.FC = () => {
  const [characterFilter, setCharacterFilter] = React.useState<string>("");
  const [seasonFilter, setSeasonFilter] = React.useState<number | undefined>(undefined);
  const [searchText, setSearchText] = React.useState<string>("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["quotes", characterFilter, seasonFilter, searchText],
    queryFn: () => fetchQuotes(
      characterFilter || undefined,
      seasonFilter,
      searchText || undefined
    ),
  });

  const quotes = data?.quotes || [];
  const total = data?.total || 0;

  // Get unique characters from quotes
  const charactersWithQuotes = React.useMemo(() => {
    const charSet = new Set<string>();
    quotes.forEach((q) => {
      if (q.character) charSet.add(q.character);
    });
    return Array.from(charSet).sort();
  }, [quotes]);

  // Get unique seasons from quotes
  const seasonsWithQuotes = React.useMemo(() => {
    const seasonSet = new Set<number>();
    quotes.forEach((q) => {
      seasonSet.add(q.season);
    });
    return Array.from(seasonSet).sort();
  }, [quotes]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Quote Explorer</h2>
        <p className="text-sm text-gray-600">
          Browse memorable quotes from the show. Filter by character, season, or search for specific text.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs font-medium text-gray-700 mb-1">Search text</label>
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search quotes..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="min-w-[150px]">
          <label className="block text-xs font-medium text-gray-700 mb-1">Character</label>
          <select
            value={characterFilter}
            onChange={(e) => setCharacterFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="">All characters</option>
            {charactersWithQuotes.map((char) => (
              <option key={char} value={char}>
                {char}
              </option>
            ))}
          </select>
        </div>
        <div className="min-w-[120px]">
          <label className="block text-xs font-medium text-gray-700 mb-1">Season</label>
          <select
            value={seasonFilter || ""}
            onChange={(e) => setSeasonFilter(e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="">All seasons</option>
            {seasonsWithQuotes.map((s) => (
              <option key={s} value={s}>
                Season {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      {isLoading && <div className="text-sm text-gray-600">Loading quotes...</div>}
      {error && (
        <div className="text-sm text-red-600">
          Failed to load quotes: {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div className="text-sm text-gray-600">
            Found {total} {total === 1 ? "quote" : "quotes"}
          </div>

          {quotes.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No quotes found matching your filters.
            </div>
          ) : (
            <div className="space-y-3">
              {quotes.map((quote) => (
                <QuoteCard key={quote.id} quote={quote} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

const QuoteCard: React.FC<{ quote: Quote }> = ({ quote }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="text-lg italic text-gray-800 mb-2">"{quote.text}"</div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
            {quote.character && (
              <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded">
                {quote.character}
              </span>
            )}
            <span>
              S{quote.season.toString().padStart(2, "0")}E{quote.episode.toString().padStart(2, "0")}: {quote.title}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

