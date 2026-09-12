import type { EpisodeLite } from "./series";
import type { GridEpisode, GridEpisodesResponse } from "./grid";

export type SeriesGridCell =
  | {
      kind: "episode";
      episode: EpisodeLite;
      episodeId: string;
      quoteCount: number;
      gridPosition?: { row: number; col: number };
    }
  | {
      kind: "empty";
      season: number;
      episode: number;
      reason: "beyond_season" | "missing_data";
    };

export type SeriesGridRow = {
  season: number;
  episodeCount: number;
  cells: SeriesGridCell[];
};

export type SeriesGridModel = {
  rows: SeriesGridRow[];
  maxEpisodesPerSeason: number;
  episodesById: Record<string, GridEpisode>;
  maxQuoteCount: number;
};

function toEpisodeLite(ep: GridEpisode): EpisodeLite {
  return {
    id: ep.id,
    season: ep.season,
    episode: ep.episode,
    title: ep.title,
    airdate: ep.airdate,
    logline: ep.logline,
    themes: ep.themes,
  };
}

function normalizeSeasonCounts(seasonCounts: Record<string, number>): Record<number, number> {
  const out: Record<number, number> = {};
  for (const [k, v] of Object.entries(seasonCounts ?? {})) {
    const n = Number(k);
    if (Number.isFinite(n)) out[n] = v;
  }
  return out;
}

export function buildSeriesGridModel(grid: GridEpisodesResponse): SeriesGridModel {
  const episodesById = grid.episodes;
  const seasonCounts = normalizeSeasonCounts(grid.metadata.season_counts);

  const seasons =
    grid.metadata.grid_dimensions?.rows ??
    Math.max(0, ...Object.values(episodesById).map((e) => e.season));
  const maxEpisodesPerSeason =
    grid.metadata.grid_dimensions?.cols ??
    grid.metadata.max_episodes_per_season ??
    Math.max(0, ...Object.values(episodesById).map((e) => e.episode));

  // Index episodes by season+episode for fast lookup
  const bySeasonEpisode = new Map<string, GridEpisode>();
  let maxQuoteCount = 0;
  for (const ep of Object.values(episodesById)) {
    bySeasonEpisode.set(`${ep.season}:${ep.episode}`, ep);
    maxQuoteCount = Math.max(maxQuoteCount, ep.metrics?.quote_count ?? 0);
  }

  const rows: SeriesGridRow[] = [];
  for (let season = 1; season <= seasons; season++) {
    const episodeCount =
      seasonCounts[season] ??
      Math.max(0, ...Object.values(episodesById).filter((e) => e.season === season).map((e) => e.episode));

    const cells: SeriesGridCell[] = [];
    for (let episode = 1; episode <= maxEpisodesPerSeason; episode++) {
      const ep = bySeasonEpisode.get(`${season}:${episode}`);

      if (!ep) {
        cells.push({
          kind: "empty",
          season,
          episode,
          reason: episode > episodeCount ? "beyond_season" : "missing_data",
        });
        continue;
      }

      cells.push({
        kind: "episode",
        episodeId: ep.id,
        episode: toEpisodeLite(ep),
        quoteCount: ep.metrics?.quote_count ?? 0,
        gridPosition: ep.grid_position,
      });
    }

    rows.push({ season, episodeCount, cells });
  }

  return {
    rows,
    maxEpisodesPerSeason,
    episodesById,
    maxQuoteCount,
  };
}


