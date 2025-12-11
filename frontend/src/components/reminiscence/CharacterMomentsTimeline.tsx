import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCharacterMoments, CharacterMoment } from "../../services/reminiscence";

const MAIN_CHARACTERS = [
  "Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia",
  "Oz", "Anya", "Faith", "Dawn", "Tara", "Riley", "Joyce",
];

interface CharacterMomentsTimelineProps {
  onNavigateToEpisode?: (episodeId: string) => void;
}

export const CharacterMomentsTimeline: React.FC<CharacterMomentsTimelineProps> = ({ onNavigateToEpisode }) => {
  const [characterFilter, setCharacterFilter] = React.useState<string>("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["character-moments", characterFilter],
    queryFn: () => fetchCharacterMoments(characterFilter || undefined),
  });

  const moments = data?.moments || [];
  const total = data?.total || 0;

  // Group moments by season
  const momentsBySeason = React.useMemo(() => {
    const grouped: Record<number, CharacterMoment[]> = {};
    moments.forEach((m) => {
      if (!grouped[m.season]) grouped[m.season] = [];
      grouped[m.season].push(m);
    });
    // Sort within each season by episode
    Object.keys(grouped).forEach((season) => {
      grouped[parseInt(season)].sort((a, b) => a.episode - b.episode);
    });
    return grouped;
  }, [moments]);

  // Get unique characters from moments
  const charactersWithMoments = React.useMemo(() => {
    const charSet = new Set<string>();
    moments.forEach((m) => {
      charSet.add(m.character);
    });
    return Array.from(charSet).sort();
  }, [moments]);

  const getMomentColor = (type: string) => {
    switch (type) {
      case "first_appearance":
        return "bg-green-500";
      case "last_appearance":
        return "bg-red-500";
      case "death":
        return "bg-black";
      default:
        return "bg-gray-500";
    }
  };

  const getMomentLabel = (type: string) => {
    switch (type) {
      case "first_appearance":
        return "First Appearance";
      case "last_appearance":
        return "Last Appearance";
      case "death":
        return "Death";
      default:
        return type;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Character Moments Timeline</h2>
        <p className="text-sm text-gray-600">
          See when characters first appeared, last appeared, or died throughout the series.
        </p>
      </div>

      {/* Filter */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <label className="block text-xs font-medium text-gray-700 mb-2">Filter by character</label>
        <select
          value={characterFilter}
          onChange={(e) => setCharacterFilter(e.target.value)}
          className="w-full max-w-xs px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
        >
          <option value="">All characters</option>
          {charactersWithMoments.map((char) => (
            <option key={char} value={char}>
              {char}
            </option>
          ))}
        </select>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>First Appearance</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Last Appearance</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-black rounded"></div>
          <span>Death</span>
        </div>
      </div>

      {/* Results */}
      {isLoading && <div className="text-sm text-gray-600">Loading moments...</div>}
      {error && (
        <div className="text-sm text-red-600">
          Failed to load moments: {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div className="text-sm text-gray-600">
            Found {total} {total === 1 ? "moment" : "moments"}
          </div>

          {moments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No moments found matching your filter.
            </div>
          ) : (
            <div className="space-y-6">
              {Object.keys(momentsBySeason)
                .sort((a, b) => parseInt(a) - parseInt(b))
                .map((season) => (
                  <SeasonTimeline
                    key={season}
                    season={parseInt(season)}
                    moments={momentsBySeason[parseInt(season)]}
                    getMomentColor={getMomentColor}
                    getMomentLabel={getMomentLabel}
                    onNavigateToEpisode={onNavigateToEpisode}
                  />
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

const SeasonTimeline: React.FC<{
  season: number;
  moments: CharacterMoment[];
  getMomentColor: (type: string) => string;
  getMomentLabel: (type: string) => string;
  onNavigateToEpisode?: (episodeId: string) => void;
}> = ({ season, moments, getMomentColor, getMomentLabel, onNavigateToEpisode }) => {
  return (
    <div className="border-l-2 border-gray-300 pl-4 space-y-3">
      <h3 className="font-semibold text-gray-800">Season {season}</h3>
      {moments.map((moment) => (
        <div
          key={moment.id}
          className="flex items-start gap-3 bg-white rounded-lg border border-gray-200 p-3 hover:shadow-md transition-shadow"
        >
          <div className={`w-3 h-3 ${getMomentColor(moment.type)} rounded-full mt-1 shrink-0`}></div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-gray-900">{moment.character}</span>
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                {getMomentLabel(moment.type)}
              </span>
            </div>
            <div 
              className="text-sm text-gray-600 cursor-pointer hover:text-blue-600 hover:underline transition-colors"
              onClick={() => onNavigateToEpisode?.(moment.episode_id)}
              title="Click to view episode details"
            >
              S{moment.season.toString().padStart(2, "0")}E{moment.episode.toString().padStart(2, "0")}: {moment.title}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

