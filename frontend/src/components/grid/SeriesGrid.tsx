import React from "react";
import * as d3 from "d3";
import type { SeriesGridModel } from "../../services/seriesGridModel";
import { GridCell } from "./GridCell";

interface SeriesGridProps {
  model: SeriesGridModel;
  selectedEpisodeId?: string;
  highlightedEpisodeIds?: string[];
  onEpisodeClick: (episodeId: string) => void;
  onEpisodeHover?: (episodeId: string | null) => void;
}

export const SeriesGrid: React.FC<SeriesGridProps> = ({
  model,
  selectedEpisodeId,
  highlightedEpisodeIds = [],
  onEpisodeClick,
  onEpisodeHover,
}) => {
  // Create color scale for quote density
  const colorScale = React.useMemo(() => {
    const maxQuotes = Math.max(model.maxQuoteCount, 1);
    return d3.scaleSequential(d3.interpolateYlOrRd).domain([0, maxQuotes]);
  }, [model.maxQuoteCount]);

  const handleHover = React.useCallback(
    (episodeId: string | null) => {
      onEpisodeHover?.(episodeId);
    },
    [onEpisodeHover]
  );

  return (
    <div className="space-y-2">
      {/* Season headers */}
      <div
        className="grid gap-2"
        style={{
          gridTemplateColumns: `repeat(${model.maxEpisodesPerSeason + 1}, minmax(0, 1fr))`,
        }}
      >
        <div className="text-xs font-semibold text-gray-500"></div>
        {Array.from({ length: model.maxEpisodesPerSeason }, (_, i) => (
          <div
            key={i}
            className="text-xs text-center text-gray-400"
            style={{ gridColumn: i + 2 }}
          >
            {i + 1}
          </div>
        ))}
      </div>

      {/* Grid rows */}
      {model.rows.map((row) => {
        const season = row.season;
        return (
          <div
            key={season}
            className="grid gap-2"
            style={{
              gridTemplateColumns: `repeat(${model.maxEpisodesPerSeason + 1}, minmax(0, 1fr))`,
            }}
          >
            {/* Season label */}
            <div className="flex items-center justify-center text-sm font-semibold text-gray-700">
              S{season}
            </div>

            {/* Episode cells */}
            {row.cells.map((cell, episodeIndex) => {
              const episodeNum = episodeIndex + 1;
              if (cell.kind === "empty") {
                return (
                  <div
                    key={`s${season}-e${episodeNum}`}
                    className="min-w-[40px] min-h-[40px] opacity-30 border border-gray-200 rounded"
                    style={{ gridColumn: episodeIndex + 2 }}
                  />
                );
              }

              const quoteCount = cell.quoteCount ?? 0;
              const backgroundColor = colorScale(quoteCount);

              return (
                <div
                  key={cell.episodeId}
                  style={{ gridColumn: episodeIndex + 2 }}
                >
                  <GridCell
                    episode={cell.episode}
                    isSelected={cell.episodeId === selectedEpisodeId}
                    isHighlighted={highlightedEpisodeIds.includes(cell.episodeId)}
                    backgroundColor={backgroundColor}
                    quoteCount={quoteCount}
                    onClick={onEpisodeClick}
                    onHover={handleHover}
                  />
                </div>
              );
            })}
          </div>
        );
      })}

      {/* Legend for quote density */}
      {model.maxQuoteCount > 0 && (
        <div className="flex items-center gap-4 mt-4 text-xs text-gray-600">
          <span>Quote density:</span>
          <div className="flex items-center gap-1">
            <div className="w-8 h-4 rounded" style={{ backgroundColor: colorScale(0) }} />
            <span>0</span>
            <div className="w-8 h-4 rounded" style={{ backgroundColor: colorScale(5) }} />
            <span>5</span>
            <div className="w-8 h-4 rounded" style={{ backgroundColor: colorScale(10) }} />
            <span>10</span>
            <div
              className="w-8 h-4 rounded"
              style={{ backgroundColor: colorScale(model.maxQuoteCount) }}
            />
            <span>max</span>
          </div>
        </div>
      )}
    </div>
  );
};
