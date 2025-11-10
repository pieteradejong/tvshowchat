import { FC, useMemo, useState } from 'react';
import { SearchResult } from '../types/search';

interface TimelineViewProps {
  results: SearchResult[];
}

interface TimelineNode {
  id: string;
  sortKey: number;
  position: number;
  season: number;
  episode: string;
  title: string;
  airdate: string;
  primary: {
    text: string;
    score: number;
    contentType: string;
    context: string;
  };
  themes: string[];
  characters: string[];
  supportingSnippets: string[];
}

const toEpisodeNumber = (episode: string) => {
  const parsed = parseInt(episode, 10);
  return Number.isNaN(parsed) ? 0 : parsed;
};

const addUnique = (collection: string[], value?: string) => {
  if (!value) return;
  if (!collection.includes(value)) {
    collection.push(value);
  }
};

const mergeUnique = (base: string[], incoming: string[]) => {
  incoming.forEach((value) => addUnique(base, value));
};

export const TimelineView: FC<TimelineViewProps> = ({ results }) => {
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  const nodes = useMemo<TimelineNode[]>(() => {
    const map = new Map<string, TimelineNode>();

    results.forEach((result, index) => {
      const key = `${result.season}-${result.episode}`;
      const existing = map.get(key);
      const numericEpisode = toEpisodeNumber(result.episode);
      const airdateTimestamp = result.airdate ? Date.parse(result.airdate) : Number.NaN;
      const sortKey = Number.isNaN(airdateTimestamp)
        ? result.season * 100 + numericEpisode
        : airdateTimestamp;

      if (!existing) {
        const supportingSnippets: string[] = [];
        if (result.snippets) {
          mergeUnique(supportingSnippets, result.snippets);
        }

        const node: TimelineNode = {
          id: key,
          sortKey,
          position: index,
          season: result.season,
          episode: result.episode,
          title: result.title,
          airdate: result.airdate,
          primary: {
            text: result.text,
            score: result.score,
            contentType: result.content_type,
            context: result.context,
          },
          themes: [...new Set(result.themes)],
          characters: [...new Set(result.characters)],
          supportingSnippets,
        };

        map.set(key, node);
        return;
      }

      // Update primary snippet if this result scores higher
      if (result.score > existing.primary.score) {
        addUnique(existing.supportingSnippets, existing.primary.text);
        existing.primary = {
          text: result.text,
          score: result.score,
          contentType: result.content_type,
          context: result.context,
        };
      } else {
        addUnique(existing.supportingSnippets, result.text);
      }

      if (result.snippets) {
        mergeUnique(existing.supportingSnippets, result.snippets);
      }

      existing.themes = [...new Set([...existing.themes, ...result.themes])];
      existing.characters = [...new Set([...existing.characters, ...result.characters])];
      existing.sortKey = Math.min(existing.sortKey, sortKey);
    });

    return Array.from(map.values()).sort((a, b) => {
      if (a.sortKey === b.sortKey) {
        return b.primary.score - a.primary.score;
      }
      return a.sortKey - b.sortKey;
    });
  }, [results]);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };

  if (nodes.length === 0) {
    return null;
  }

  return (
    <div className="relative">
      <div className="absolute left-3 top-0 h-full w-px bg-blue-100" aria-hidden />
      <div className="space-y-6">
        {nodes.map((node, index) => {
          const isExpanded = expandedNodes[node.id] ?? false;
          const contextPieces = node.primary.context
            ? node.primary.context.split('|').map((chunk) => chunk.trim()).filter(Boolean)
            : [];

          return (
            <div key={node.id} className="relative pl-12">
              <span
                className="absolute left-1 top-3 flex h-5 w-5 items-center justify-center rounded-full border-2 border-blue-500 bg-blue-50 text-xs font-semibold text-blue-700"
                aria-hidden
              >
                {index + 1}
              </span>

              <div className="rounded-lg border border-blue-100 bg-white p-4 shadow-sm">
                <header className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">
                      S{String(node.season).padStart(2, '0')}E{node.episode}. {node.title}
                    </h3>
                    <p className="text-xs text-gray-500">{node.airdate || 'Airdate unknown'}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span className="rounded bg-blue-50 px-2 py-1 uppercase tracking-wide text-blue-600">
                      {node.primary.contentType}
                    </span>
                    <span className="rounded bg-amber-50 px-2 py-1 font-semibold text-amber-700">
                      {Math.round(node.primary.score * 100)}%
                    </span>
                  </div>
                </header>

                <div className="mt-3 space-y-2">
                  <p className="rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3 text-sm leading-relaxed text-gray-800">
                    {node.primary.text}
                  </p>

                  {(node.themes.length > 0 || node.characters.length > 0) && (
                    <div className="flex flex-wrap gap-2 text-xs">
                      {node.themes.slice(0, 4).map((theme) => (
                        <span
                          key={`theme-${node.id}-${theme}`}
                          className="rounded-full bg-green-50 px-3 py-1 font-medium text-green-700"
                        >
                          #{theme}
                        </span>
                      ))}
                      {node.characters.slice(0, 4).map((character) => (
                        <span
                          key={`character-${node.id}-${character}`}
                          className="rounded-full bg-blue-50 px-3 py-1 font-medium text-blue-700"
                        >
                          {character}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {(contextPieces.length > 0 || node.supportingSnippets.length > 0) && (
                  <div className="mt-4 border-t border-gray-100 pt-3">
                    <button
                      type="button"
                      onClick={() => toggleNode(node.id)}
                      className="text-sm font-medium text-blue-600 transition hover:text-blue-800"
                    >
                      {isExpanded ? 'Hide details' : 'Show details'}
                    </button>

                    {isExpanded && (
                      <div className="mt-3 space-y-3 text-sm text-gray-700">
                        {contextPieces.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                              Context
                            </p>
                            <ul className="mt-1 space-y-1">
                              {contextPieces.map((piece, pieceIndex) => (
                                <li key={`${node.id}-context-${pieceIndex}`}>{piece}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {node.supportingSnippets.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                              Supporting snippets
                            </p>
                            <ul className="mt-2 space-y-2">
                              {node.supportingSnippets.map((snippet, snippetIndex) => (
                                <li
                                  key={`${node.id}-snippet-${snippetIndex}`}
                                  className="rounded-md border border-gray-200 bg-gray-50 p-3 text-gray-700"
                                >
                                  {snippet}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
