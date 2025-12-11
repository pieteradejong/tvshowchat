import React from "react";
import type { EpisodeLite } from "../services/series";

type Props = {
  episodes: EpisodeLite[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onHover?: (id?: string) => void;
};

export const SeriesTimeline: React.FC<Props> = ({ episodes, selectedId, onSelect, onHover }) => {
  const [collapsedSeasons, setCollapsedSeasons] = React.useState<Set<number>>(new Set());

  const seasons = React.useMemo(() => {
    const m = new Map<number, EpisodeLite[]>();
    episodes.forEach((e) => {
      if (!m.has(e.season)) m.set(e.season, []);
      m.get(e.season)!.push(e);
    });
    for (const list of m.values()) list.sort((a, b) => a.episode - b.episode);
    return Array.from(m.entries()).sort((a, b) => a[0] - b[0]);
  }, [episodes]);

  const toggleSeason = (season: number) => {
    setCollapsedSeasons((prev) => {
      const next = new Set(prev);
      if (next.has(season)) {
        next.delete(season);
      } else {
        next.add(season);
      }
      return next;
    });
  };

  // Auto-expand season if selected episode is in it
  React.useEffect(() => {
    if (!selectedId) return;
    const selected = episodes.find((e) => e.id === selectedId);
    if (selected) {
      setCollapsedSeasons((prev) => {
        const next = new Set(prev);
        next.delete(selected.season);
        return next;
      });
    }
  }, [selectedId, episodes]);

  return (
    <div className="flex flex-col gap-3" role="region" aria-label="Episode timeline">
      {seasons.map(([season, eps]) => {
        const isCollapsed = collapsedSeasons.has(season);
        return (
          <div key={season} className="flex items-start gap-2">
            <button
              onClick={() => toggleSeason(season)}
              aria-label={`${isCollapsed ? "Expand" : "Collapse"} season ${season}`}
              className="w-12 shrink-0 text-sm font-semibold hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded px-1"
            >
              <span className="inline-block mr-1">{isCollapsed ? "▶" : "▼"}</span>
              <span>S{season}</span>
            </button>
            {!isCollapsed && (
              <div className="flex flex-wrap gap-4">
                {eps.map((e) => {
                  const isSelected = e.id === selectedId;
                  return (
                    <button
                      key={e.id}
                      aria-label={`Episode ${e.episode}: ${e.title}`}
                      aria-pressed={isSelected}
                      onClick={() => onSelect(e.id)}
                      onMouseEnter={() => onHover?.(e.id)}
                      onMouseLeave={() => onHover?.(undefined)}
                      className={`px-2 py-1 rounded text-xs border transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
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
            )}
          </div>
        );
      })}
    </div>
  );
};


