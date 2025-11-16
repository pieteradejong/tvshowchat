import React from "react";
import type { EpisodeLite } from "../services/series";

type Props = {
  episodes: EpisodeLite[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onHover?: (id?: string) => void;
};

export const SeriesTimeline: React.FC<Props> = ({ episodes, selectedId, onSelect, onHover }) => {
  const seasons = React.useMemo(() => {
    const m = new Map<number, EpisodeLite[]>();
    episodes.forEach((e) => {
      if (!m.has(e.season)) m.set(e.season, []);
      m.get(e.season)!.push(e);
    });
    for (const list of m.values()) list.sort((a, b) => a.episode - b.episode);
    return Array.from(m.entries()).sort((a, b) => a[0] - b[0]);
  }, [episodes]);

  return (
    <div className="flex flex-col gap-3">
      {seasons.map(([season, eps]) => (
        <div key={season} className="flex items-center gap-2">
          <div className="w-12 shrink-0 text-sm font-semibold">S{season}</div>
          <div className="flex flex-wrap gap-4">
            {eps.map((e) => {
              const isSelected = e.id === selectedId;
              return (
                <button
                  key={e.id}
                  aria-label={`${e.title}`}
                  onClick={() => onSelect(e.id)}
                  onMouseEnter={() => onHover?.(e.id)}
                  onMouseLeave={() => onHover?.(undefined)}
                  className={`px-2 py-1 rounded text-xs border ${
                    isSelected
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white hover:bg-indigo-50 border-gray-200"
                  }`}
                  title={`${e.title} — ${e.logline}`}
                >
                  E{e.episode}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};


