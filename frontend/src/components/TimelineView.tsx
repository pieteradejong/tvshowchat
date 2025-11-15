import { FC, useMemo, useState, useEffect, useRef } from 'react';
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
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Group nodes by season for season markers
  const nodesBySeason = useMemo(() => {
    const map = new Map<string, TimelineNode>();
    const seasonGroups = new Map<number, TimelineNode[]>();

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

    const sortedNodes = Array.from(map.values()).sort((a, b) => {
      if (a.sortKey === b.sortKey) {
        return b.primary.score - a.primary.score;
      }
      return a.sortKey - b.sortKey;
    });

    // Group by season
    sortedNodes.forEach((node) => {
      if (!seasonGroups.has(node.season)) {
        seasonGroups.set(node.season, []);
      }
      seasonGroups.get(node.season)!.push(node);
    });

    return { nodes: sortedNodes, seasonGroups };
  }, [results]);

  const { nodes, seasonGroups } = nodesBySeason;

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (nodes.length === 0) return;

      const currentIndex = focusedNodeId
        ? nodes.findIndex((n) => n.id === focusedNodeId)
        : -1;

      let nextIndex = currentIndex;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        nextIndex = currentIndex < nodes.length - 1 ? currentIndex + 1 : 0;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        nextIndex = currentIndex > 0 ? currentIndex - 1 : nodes.length - 1;
      } else if (e.key === 'Enter' || e.key === ' ') {
        if (focusedNodeId) {
          e.preventDefault();
          toggleNode(focusedNodeId);
        }
      } else if (e.key === 'Escape') {
        setFocusedNodeId(null);
      }

      if (nextIndex !== currentIndex && nextIndex >= 0) {
        const nextNode = nodes[nextIndex];
        setFocusedNodeId(nextNode.id);
        nodeRefs.current[nextNode.id]?.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusedNodeId, nodes, toggleNode]);

  if (nodes.length === 0) {
    return null;
  }

  // Format airdate for display
  const formatAirdate = (airdate: string) => {
    if (!airdate) return 'Airdate unknown';
    try {
      const date = new Date(airdate);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return airdate;
    }
  };

  return (
    <div className="relative">
      {/* Enhanced timeline spine with gradient */}
      <div className="absolute left-3 sm:left-4 top-0 h-full w-0.5 bg-gradient-to-b from-blue-200 via-blue-300 to-blue-200" aria-hidden />
      
      <div className="space-y-6 sm:space-y-8">
        {Array.from(seasonGroups.entries())
          .sort(([a], [b]) => a - b)
          .map(([season, seasonNodes]) => (
            <div key={`season-${season}`} className="relative">
              {/* Season header */}
              <div className="sticky top-0 z-10 mb-4 bg-white/95 backdrop-blur-sm py-2 border-b-2 border-blue-200">
                <h2 className="text-lg sm:text-xl font-bold text-blue-900 flex items-center gap-2">
                  <span className="flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full bg-blue-600 text-white text-xs sm:text-sm font-bold">
                    {season}
                  </span>
                  <span>Season {season}</span>
                  <span className="text-sm font-normal text-gray-500">
                    ({seasonNodes.length} {seasonNodes.length === 1 ? 'episode' : 'episodes'})
                  </span>
                </h2>
              </div>

              {/* Season episodes */}
              <div className="space-y-4 sm:space-y-6 pl-2">
                {seasonNodes.map((node, nodeIndex) => {
                  const isExpanded = expandedNodes[node.id] ?? false;
                  const isFocused = focusedNodeId === node.id;
                  const contextPieces = node.primary.context
                    ? node.primary.context.split('|').map((chunk) => chunk.trim()).filter(Boolean)
                    : [];
                  const globalIndex = nodes.findIndex((n) => n.id === node.id);

                  return (
                    <div
                      key={node.id}
                      ref={(el) => {
                        nodeRefs.current[node.id] = el;
                      }}
                      className={`relative pl-8 sm:pl-12 transition-all ${
                        isFocused ? 'ring-2 ring-blue-500 ring-offset-2 rounded-lg' : ''
                      }`}
                      tabIndex={0}
                      onFocus={() => setFocusedNodeId(node.id)}
                      onBlur={() => {
                        // Don't blur if clicking inside the node
                        if (!nodeRefs.current[node.id]?.contains(document.activeElement)) {
                          setFocusedNodeId(null);
                        }
                      }}
                    >
                      {/* Enhanced episode marker */}
                      <span
                        className={`absolute left-0 sm:left-1 top-4 flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full border-2 text-xs sm:text-sm font-bold transition-all ${
                          isFocused
                            ? 'border-blue-600 bg-blue-600 text-white scale-110'
                            : 'border-blue-500 bg-blue-50 text-blue-700 hover:border-blue-600 hover:bg-blue-100'
                        }`}
                        aria-hidden
                      >
                        {globalIndex + 1}
                      </span>

                      <div className={`rounded-lg border-2 bg-white p-4 sm:p-5 shadow-md transition-all ${
                        isFocused
                          ? 'border-blue-400 shadow-lg'
                          : 'border-blue-100 hover:border-blue-200 hover:shadow-lg'
                      }`}>
                        <header className="flex flex-col sm:flex-row sm:flex-wrap sm:items-start sm:justify-between gap-3 sm:gap-4 mb-3">
                          <div className="flex-1">
                            <h3 className="text-base sm:text-lg font-bold text-gray-900 mb-1">
                              S{String(node.season).padStart(2, '0')}E{node.episode}. {node.title}
                            </h3>
                            <p className="text-xs sm:text-sm text-gray-600 flex items-center gap-2">
                              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {formatAirdate(node.airdate)}
                            </p>
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-700 border border-blue-200">
                              {node.primary.contentType}
                            </span>
                            <span className="rounded-full bg-gradient-to-r from-amber-400 to-amber-500 px-3 py-1 text-xs font-bold text-white shadow-sm">
                              {Math.round(node.primary.score * 100)}%
                            </span>
                          </div>
                        </header>

                        <div className="space-y-3">
                          <p className="rounded-lg border-l-4 border-amber-400 bg-gradient-to-r from-amber-50 to-amber-100/50 p-3 sm:p-4 text-sm sm:text-base leading-relaxed text-gray-800 break-words shadow-sm">
                            {node.primary.text}
                          </p>

                          {(node.themes.length > 0 || node.characters.length > 0) && (
                            <div className="flex flex-wrap gap-2">
                              {node.themes.slice(0, 6).map((theme) => (
                                <span
                                  key={`theme-${node.id}-${theme}`}
                                  className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-green-100 to-green-50 px-3 py-1.5 text-xs font-semibold text-green-800 border border-green-200 shadow-sm"
                                >
                                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M9.243 3.03a1 1 0 01.707 0l4 1a1 1 0 11-.514 1.93L10 4.88l-3.436.08a1 1 0 11-.514-1.93l4-1zM5.88 6.757a1 1 0 011.214-.97l3.5.875a1 1 0 01.612.97v6.5a1 1 0 01-1.214.97l-3.5-.875a1 1 0 01-.612-.97V6.757zM3 10a1 1 0 011-1h.5a1 1 0 010 2H4a1 1 0 01-1-1zm14 0a1 1 0 01-1-1h-.5a1 1 0 110 2H16a1 1 0 01-1-1z" clipRule="evenodd" />
                                      </svg>
                                      {theme}
                                    </span>
                              ))}
                              {node.characters.slice(0, 6).map((character) => (
                                <span
                                  key={`character-${node.id}-${character}`}
                                  className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-blue-100 to-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-800 border border-blue-200 shadow-sm"
                                >
                                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                                      </svg>
                                      {character}
                                    </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {(contextPieces.length > 0 || node.supportingSnippets.length > 0) && (
                          <div className="mt-4 border-t-2 border-gray-200 pt-4">
                            <button
                              type="button"
                              onClick={() => toggleNode(node.id)}
                              className="flex items-center gap-2 text-sm font-semibold text-blue-600 transition hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-2 py-1"
                              aria-expanded={isExpanded}
                            >
                              <svg
                                className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                              {isExpanded ? 'Hide details' : 'Show details'}
                            </button>

                            {isExpanded && (
                              <div className="mt-4 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
                                {contextPieces.length > 0 && (
                                  <div className="rounded-lg bg-blue-50/50 border border-blue-100 p-3 sm:p-4">
                                    <p className="text-xs font-bold uppercase tracking-wide text-blue-700 mb-2 flex items-center gap-2">
                                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                      </svg>
                                      Context
                                    </p>
                                    <ul className="mt-2 space-y-2">
                                      {contextPieces.map((piece, pieceIndex) => (
                                        <li key={`${node.id}-context-${pieceIndex}`} className="text-sm text-gray-700 break-words pl-2 border-l-2 border-blue-300">
                                          {piece}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {node.supportingSnippets.length > 0 && (
                                  <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 sm:p-4">
                                    <p className="text-xs font-bold uppercase tracking-wide text-gray-600 mb-3 flex items-center gap-2">
                                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                                        <path fillRule="evenodd" d="M4 5h2a1 1 0 010 2H4a1 1 0 01-1-1V5zM4 11a1 1 0 011-1h12a1 1 0 110 2H5a1 1 0 01-1-1zM16 13H4a1 1 0 100 2h12a1 1 0 100-2z" clipRule="evenodd" />
                                      </svg>
                                      Supporting snippets ({node.supportingSnippets.length})
                                    </p>
                                    <ul className="mt-2 space-y-3">
                                      {node.supportingSnippets.map((snippet, snippetIndex) => (
                                        <li
                                          key={`${node.id}-snippet-${snippetIndex}`}
                                          className="rounded-md border border-gray-300 bg-white p-3 sm:p-4 text-sm text-gray-700 break-words shadow-sm hover:shadow transition-shadow"
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
          ))}
      </div>
      
      {/* Keyboard navigation hint */}
      {nodes.length > 0 && (
        <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700">
          <p className="font-semibold mb-1">Keyboard shortcuts:</p>
          <ul className="space-y-1 text-blue-600">
            <li>↑↓ Arrow keys to navigate</li>
            <li>Enter/Space to expand/collapse</li>
            <li>Esc to clear focus</li>
          </ul>
        </div>
      )}
    </div>
  );
};
