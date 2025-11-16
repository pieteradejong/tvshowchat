import React from "react";
import type { EpisodeLite } from "../services/series";

type Props = {
  episode?: EpisodeLite;
};

export const EpisodeDetailCard: React.FC<Props> = ({ episode }) => {
  if (!episode) {
    return (
      <div className="p-4 rounded border border-gray-200 text-sm text-gray-600">
        Select an episode to see details.
      </div>
    );
  }
  return (
    <div className="p-4 rounded border border-gray-200 bg-white">
      <div className="text-xs text-gray-500">
        S{episode.season} • E{episode.episode} • {episode.airdate}
      </div>
      <h3 className="mt-1 text-lg font-semibold">{episode.title}</h3>
      <p className="mt-2 text-sm text-gray-800">{episode.logline}</p>
      {episode.themes?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {episode.themes.slice(0, 5).map((t) => (
            <span
              key={t}
              className="px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-700 border border-indigo-100"
            >
              {t}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
};


