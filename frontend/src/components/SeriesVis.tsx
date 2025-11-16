import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCharacterArcs, fetchEpisodes, EpisodeLite } from "../services/series";
import { SeriesTimeline } from "./SeriesTimeline";
import { CharacterSparklines } from "./CharacterSparklines";
import { EpisodeDetailCard } from "./EpisodeDetailCard";

export const SeriesVis: React.FC = () => {
  const { data: episodes, isLoading: epLoading, error: epError } = useQuery({
    queryKey: ["series-episodes"],
    queryFn: fetchEpisodes,
  });
  const { data: arcs, isLoading: arcLoading, error: arcError } = useQuery({
    queryKey: ["series-arcs"],
    queryFn: fetchCharacterArcs,
  });

  const [selectedId, setSelectedId] = React.useState<string | undefined>(undefined);
  const [hoverId, setHoverId] = React.useState<string | undefined>(undefined);
  const detailRef = React.useRef<HTMLDivElement | null>(null);

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

  // Auto-scroll detail card into view on selection (esp. mobile)
  React.useEffect(() => {
    if (!selectedId) return;
    const el = detailRef.current;
    if (!el) return;
    // Prefer smooth scroll; on narrow screens ensure visibility
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selectedId]);

  if (epLoading || arcLoading) {
    return <div className="text-sm text-gray-600">Loading series data…</div>;
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
        <h2 className="text-base font-semibold text-gray-800">Episode timeline</h2>
        <SeriesTimeline
          episodes={episodes}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onHover={setHoverId}
        />

        <h2 className="mt-4 text-base font-semibold text-gray-800">Character arcs</h2>
        <CharacterSparklines arcs={arcs} episodesOrder={episodesOrder} highlightEpisodeId={hoverId || selectedId} />
      </div>
      <div className="lg:col-span-1">
        <h2 className="text-base font-semibold text-gray-800 mb-2">Episode detail</h2>
        <div ref={detailRef}>
          <EpisodeDetailCard episode={selectedEpisode} />
        </div>
      </div>
    </div>
  );
};


