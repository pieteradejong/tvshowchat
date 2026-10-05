const API_BASE = "/api";

export type QuoteDensity = Record<string, number>; // episode_id -> quote count

export interface GridPosition {
  row: number;
  col: number;
}

export interface EpisodeMetrics {
  quote_count: number;
  character_presence: Record<string, number>;
  character_moments: {
    first_appearances: string[];
    last_appearances: string[];
    deaths: string[];
  };
}

export interface GridEpisode {
  id: string;
  season: number;
  episode: number;
  title: string;
  airdate: string;
  logline: string;
  themes: string[];
  grid_position: GridPosition;
  metrics: EpisodeMetrics;
}

export interface GridMetadata {
  total_episodes: number;
  // Note: JSON object keys are always strings, even if backend uses ints.
  season_counts: Record<string, number>;
  max_episodes_per_season: number;
  grid_dimensions: {
    rows: number;
    cols: number;
  };
}

export interface GridEpisodesResponse {
  episodes: Record<string, GridEpisode>;
  metadata: GridMetadata;
}

export async function fetchQuoteDensity(): Promise<QuoteDensity> {
  const res = await fetch(`${API_BASE}/grid/quotes-density`);
  if (!res.ok) throw new Error(`Failed to fetch quote density: ${res.status}`);
  return res.json();
}

export async function fetchGridEpisodes(): Promise<GridEpisodesResponse> {
  const res = await fetch(`${API_BASE}/grid/episodes`);
  if (!res.ok) throw new Error(`Failed to fetch grid episodes: ${res.status}`);
  return res.json();
}
