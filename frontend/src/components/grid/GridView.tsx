import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchGridEpisodes } from "../../services/grid";
import { buildSeriesGridModel } from "../../services/seriesGridModel";
import { SeriesGrid } from "./SeriesGrid";

interface GridViewProps {
  onNavigateToEpisode?: (episodeId: string) => void;
}

export const GridView: React.FC<GridViewProps> = ({ onNavigateToEpisode }) => {
  const [selectedEpisodeId, setSelectedEpisodeId] = React.useState<string | undefined>();
  const [, setHoveredEpisodeId] = React.useState<string | null>(null);

  const { data: gridData, isLoading, error } = useQuery({
    queryKey: ["grid-episodes"],
    queryFn: fetchGridEpisodes,
  });

  const handleEpisodeClick = React.useCallback(
    (episodeId: string) => {
      setSelectedEpisodeId(episodeId);
      onNavigateToEpisode?.(episodeId);
      // Update URL hash for deep linking
      window.location.hash = episodeId;
    },
    [onNavigateToEpisode]
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">Loading grid data…</div>
        <div className="flex flex-col gap-2">
          {[1, 2, 3, 4, 5, 6, 7].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div className="w-12 shrink-0 text-sm font-semibold text-gray-400">S{s}</div>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-10 h-10 bg-gray-200 rounded animate-pulse"
                    aria-hidden="true"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Failed to load data. {error?.message}
      </div>
    );
  }

  if (!gridData) {
    return <div className="text-sm text-gray-600">No data available.</div>;
  }

  const model = buildSeriesGridModel(gridData);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Series Grid</h1>
        <p className="text-sm text-gray-600">
          Visualize the complete series in a grid layout. Each cell represents an episode.
          Color intensity shows quote density. Click an episode to view details.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 overflow-x-auto">
        <SeriesGrid
          model={model}
          selectedEpisodeId={selectedEpisodeId}
          onEpisodeClick={handleEpisodeClick}
          onEpisodeHover={setHoveredEpisodeId}
        />
      </div>

      {selectedEpisodeId && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Selected Episode</h2>
          <p className="text-sm text-gray-600">
            Episode ID: {selectedEpisodeId}
            <br />
            Use arrow keys to navigate between episodes (coming soon).
          </p>
        </div>
      )}
    </div>
  );
};
