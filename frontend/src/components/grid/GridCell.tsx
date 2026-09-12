import React from "react";
import type { EpisodeLite } from "../../services/series";

interface GridCellProps {
  episode: EpisodeLite;
  isSelected: boolean;
  isHighlighted?: boolean;
  backgroundColor?: string;
  quoteCount?: number;
  onClick: (episodeId: string) => void;
  onHover: (episodeId: string | null) => void;
}

export const GridCell: React.FC<GridCellProps> = ({
  episode,
  isSelected,
  isHighlighted = false,
  backgroundColor = "white",
  quoteCount,
  onClick,
  onHover,
}) => {
  const handleClick = () => {
    onClick(episode.id);
  };

  const handleMouseEnter = () => {
    onHover(episode.id);
  };

  const handleMouseLeave = () => {
    onHover(null);
  };

  return (
    <button
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`
        relative w-full h-full min-w-[40px] min-h-[40px]
        border transition-all duration-150
        flex items-center justify-center
        text-xs font-medium
        hover:scale-105 hover:z-10
        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1
        ${isSelected ? "ring-2 ring-indigo-600 ring-offset-1 z-20" : ""}
        ${isHighlighted ? "ring-2 ring-blue-500 ring-offset-1" : ""}
      `}
      style={{
        backgroundColor,
      }}
      title={`S${episode.season}E${episode.episode}: ${episode.title}\n${episode.logline}`}
      aria-label={`Episode ${episode.episode}: ${episode.title}`}
    >
      <span className="text-gray-700">E{episode.episode}</span>
      {quoteCount !== undefined && quoteCount > 0 && (
        <span
          className="absolute top-0 right-0 bg-indigo-600 text-white text-[10px] px-1 rounded-bl"
          title={`${quoteCount} quotes`}
        >
          {quoteCount}
        </span>
      )}
    </button>
  );
};
