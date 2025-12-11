import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchCharacterRelationships,
  fetchThemeCooccurrence,
  fetchEpisodeSimilarity,
  fetchCharacterJourney,
  fetchTemporalArcs,
} from "../services/experiments";
import { CharacterNetwork } from "./experiments/CharacterNetwork";
import { ThemeCooccurrenceMatrix } from "./experiments/ThemeCooccurrenceMatrix";
import { EpisodeSimilarityMap } from "./experiments/EpisodeSimilarityMap";
import { CharacterJourneySankey } from "./experiments/CharacterJourneySankey";
import { TemporalArcExplorer } from "./experiments/TemporalArcExplorer";

export const Experiments: React.FC = () => {
  const [activeViz, setActiveViz] = React.useState<string>("network");

  const { data: relationships, isLoading: relLoading } = useQuery({
    queryKey: ["experiments-relationships"],
    queryFn: fetchCharacterRelationships,
  });

  const { data: themes, isLoading: themesLoading } = useQuery({
    queryKey: ["experiments-themes"],
    queryFn: fetchThemeCooccurrence,
  });

  const { data: similarity, isLoading: simLoading } = useQuery({
    queryKey: ["experiments-similarity"],
    queryFn: fetchEpisodeSimilarity,
  });

  const { data: journey, isLoading: journeyLoading } = useQuery({
    queryKey: ["experiments-journey"],
    queryFn: fetchCharacterJourney,
  });

  const { data: temporal, isLoading: temporalLoading } = useQuery({
    queryKey: ["experiments-temporal"],
    queryFn: fetchTemporalArcs,
  });

  const vizOptions = [
    { id: "network", name: "Character Network", icon: "🕸️" },
    { id: "themes", name: "Theme Co-occurrence", icon: "🔥" },
    { id: "similarity", name: "Episode Similarity", icon: "🗺️" },
    { id: "journey", name: "Character Journey", icon: "🌊" },
    { id: "temporal", name: "Temporal Arcs", icon: "📈" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Data Visualization Experiments</h1>
        <p className="text-sm text-gray-600">
          Interactive visualizations exploring characters, relationships, themes, and narrative structure
        </p>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-gray-200 pb-4">
        {vizOptions.map((viz) => (
          <button
            key={viz.id}
            onClick={() => setActiveViz(viz.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeViz === viz.id
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <span className="mr-2">{viz.icon}</span>
            {viz.name}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 min-h-[600px]">
        {activeViz === "network" && (
          <CharacterNetwork
            data={relationships}
            isLoading={relLoading}
          />
        )}
        {activeViz === "themes" && (
          <ThemeCooccurrenceMatrix
            data={themes}
            isLoading={themesLoading}
          />
        )}
        {activeViz === "similarity" && (
          <EpisodeSimilarityMap
            data={similarity}
            isLoading={simLoading}
          />
        )}
        {activeViz === "journey" && (
          <CharacterJourneySankey
            data={journey}
            isLoading={journeyLoading}
          />
        )}
        {activeViz === "temporal" && (
          <TemporalArcExplorer
            data={temporal}
            isLoading={temporalLoading}
          />
        )}
      </div>
    </div>
  );
};


