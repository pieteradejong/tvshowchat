import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSeasonComparison, SeasonStats } from "../../services/reminiscence";

export const SeasonComparison: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["season-comparison"],
    queryFn: fetchSeasonComparison,
  });

  const seasons = data?.seasons || {};

  const seasonNumbers = React.useMemo(() => {
    return Object.keys(seasons)
      .map((s) => parseInt(s))
      .sort((a, b) => a - b);
  }, [seasons]);

  // Get all characters across all seasons for consistent comparison
  const allCharacters = React.useMemo(() => {
    const charSet = new Set<string>();
    Object.values(seasons).forEach((stats: SeasonStats) => {
      Object.keys(stats.characters || {}).forEach((char) => charSet.add(char));
    });
    return Array.from(charSet).sort();
  }, [seasons]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Season Comparison</h2>
        <p className="text-sm text-gray-600">
          Compare seasons side-by-side: episode counts, character presence, and themes.
        </p>
      </div>

      {isLoading && <div className="text-sm text-gray-600">Loading season data...</div>}
      {error && (
        <div className="text-sm text-red-600">
          Failed to load season comparison: {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && seasonNumbers.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {seasonNumbers.map((seasonNum) => {
            const stats = seasons[seasonNum.toString()] as SeasonStats;
            return <SeasonCard key={seasonNum} season={seasonNum} stats={stats} allCharacters={allCharacters} />;
          })}
        </div>
      )}
    </div>
  );
};

const SeasonCard: React.FC<{
  season: number;
  stats: SeasonStats;
  allCharacters: string[];
}> = ({ season, stats, allCharacters }) => {
  const topCharacters = React.useMemo(() => {
    return Object.entries(stats.characters || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  }, [stats.characters]);

  const topThemes = React.useMemo(() => {
    return stats.themes.slice(0, 5);
  }, [stats.themes]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 mb-1">Season {season}</h3>
        <div className="text-sm text-gray-600">
          {stats.episode_count} {stats.episode_count === 1 ? "episode" : "episodes"}
        </div>
      </div>

      {/* Top Characters */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Top Characters</h4>
        <div className="space-y-1">
          {topCharacters.length > 0 ? (
            topCharacters.map(([char, count]) => (
              <div key={char} className="flex items-center justify-between text-xs">
                <span className="text-gray-700">{char}</span>
                <span className="text-gray-500">{count}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-400">No character data</div>
          )}
        </div>
      </div>

      {/* Top Themes */}
      <div>
        <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Top Themes</h4>
        <div className="flex flex-wrap gap-1">
          {topThemes.length > 0 ? (
            topThemes.map((theme) => (
              <span
                key={theme}
                className="text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded"
              >
                {theme}
              </span>
            ))
          ) : (
            <div className="text-xs text-gray-400">No theme data</div>
          )}
        </div>
      </div>
    </div>
  );
};

