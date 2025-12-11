import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCharacterArcs, fetchEpisodes, EpisodeLite } from "../services/series";
import { SeriesTimeline } from "./SeriesTimeline";
import { CharacterSparklines } from "./CharacterSparklines";
import { EpisodeDetailCard } from "./EpisodeDetailCard";

// Parse episode ID from URL hash (e.g., #s02e14 -> "s02e14")
function parseHashEpisodeId(): string | undefined {
  if (typeof window === "undefined") return undefined;
  const hash = window.location.hash.slice(1);
  if (!hash.match(/^s\d+e\d+$/)) return undefined;
  return hash;
}

// Update URL hash when episode is selected
function updateHash(episodeId: string | undefined) {
  if (typeof window === "undefined") return;
  if (episodeId) {
    window.history.replaceState(null, "", `#${episodeId}`);
  } else {
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }
}

export const SeriesVis: React.FC = () => {
  const { data: episodes, isLoading: epLoading, error: epError } = useQuery({
    queryKey: ["series-episodes"],
    queryFn: fetchEpisodes,
  });
  const { data: arcs, isLoading: arcLoading, error: arcError } = useQuery({
    queryKey: ["series-arcs"],
    queryFn: fetchCharacterArcs,
  });

  const [selectedId, setSelectedId] = React.useState<string | undefined>(() => parseHashEpisodeId());
  const [hoverId, setHoverId] = React.useState<string | undefined>(undefined);
  const detailRef = React.useRef<HTMLDivElement | null>(null);
  const timelineRef = React.useRef<HTMLDivElement | null>(null);

  const episodesOrder = React.useMemo(() => {
    if (!episodes) return [];
    return [...episodes]
      .sort((a, b) => (a.season - b.season) || (a.episode - b.episode))
      .map((e) => e.id);
  }, [episodes]);

  const selectedEpisode: EpisodeLite | undefined = React.useMemo(() => {
    if (!episodes || !selectedId) return undefined;
    return episodes.find((e) => e.id === selectedId);
  }, [episodes, selectedId]);

  // Hydrate selection from URL hash on mount
  React.useEffect(() => {
    if (!episodes) return;
    const hashId = parseHashEpisodeId();
    if (hashId && episodes.some((e) => e.id === hashId)) {
      setSelectedId(hashId);
    }
  }, [episodes]);

  // Update URL hash when selection changes
  React.useEffect(() => {
    updateHash(selectedId);
  }, [selectedId]);

  // Auto-scroll detail card into view on selection (esp. mobile)
  React.useEffect(() => {
    if (!selectedId) return;
    const el = detailRef.current;
    if (!el) return;
    // Prefer smooth scroll; on narrow screens ensure visibility
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selectedId]);

  // Keyboard navigation: arrow keys to move selection, Enter to focus detail
  React.useEffect(() => {
    if (!episodes || episodesOrder.length === 0) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedId) return;
      const currentIdx = episodesOrder.indexOf(selectedId);
      if (currentIdx === -1) return;

      let nextId: string | undefined;
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextId = episodesOrder[currentIdx - 1];
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextId = episodesOrder[currentIdx + 1];
      } else if (e.key === "Enter" && selectedId) {
        e.preventDefault();
        detailRef.current?.focus();
        return;
      }
      if (nextId) setSelectedId(nextId);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [episodes, episodesOrder, selectedId]);

  if (epLoading || arcLoading) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">Loading series data…</div>
        <div className="flex flex-col gap-3">
          {[1, 2, 3, 4, 5, 6, 7].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div className="w-12 shrink-0 text-sm font-semibold text-gray-400">S{s}</div>
              <div className="flex flex-wrap gap-4">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-12 h-6 bg-gray-200 rounded animate-pulse"
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
  if (epError || arcError) {
    return (
      <div className="text-sm text-red-600">
        Failed to load data. {(epError as any)?.message || (arcError as any)?.message}
      </div>
    );
  }
  if (!episodes || !arcs) {
    return <div className="text-sm text-gray-600">No data available.</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-base font-semibold text-gray-800">Episode timeline</h2>
          <div className="flex items-center gap-3">
            {episodes && (
              <select
                onChange={(e) => {
                  const season = parseInt(e.target.value);
                  if (season && episodes.length > 0) {
                    const firstInSeason = episodes
                      .filter((ep) => ep.season === season)
                      .sort((a, b) => a.episode - b.episode)[0];
                    if (firstInSeason) setSelectedId(firstInSeason.id);
                  }
                }}
                className="text-xs border border-gray-300 rounded px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                aria-label="Jump to season"
              >
                <option value="">Jump to season…</option>
                {Array.from(new Set(episodes.map((e) => e.season)))
                  .sort((a, b) => a - b)
                  .map((s) => (
                    <option key={s} value={s}>
                      Season {s}
                    </option>
                  ))}
              </select>
            )}
            <div className="text-xs text-gray-500">
              Use arrow keys to navigate, Enter to focus detail
            </div>
          </div>
        </div>
        <div ref={timelineRef}>
          <SeriesTimeline
            episodes={episodes}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onHover={setHoverId}
          />
        </div>

        <h2 className="mt-4 text-base font-semibold text-gray-800">Character arcs</h2>
        <CharacterSparklines arcs={arcs} episodesOrder={episodesOrder} highlightEpisodeId={hoverId || selectedId} />
      </div>
      <div className="lg:col-span-1">
        <h2 className="text-base font-semibold text-gray-800 mb-2">Episode detail</h2>
        <div ref={detailRef} tabIndex={-1} aria-label="Episode details">
          <EpisodeDetailCard episode={selectedEpisode} />
        </div>
      </div>
    </div>
  );
};


