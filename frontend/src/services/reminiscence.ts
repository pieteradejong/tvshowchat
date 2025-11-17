const API_BASE = "/api";

export type Quote = {
  id: string;
  episode_id: string;
  text: string;
  character: string | null;
  season: number;
  episode: number;
  title: string;
};

export type QuotesResponse = {
  quotes: Quote[];
  total: number;
};

export type CharacterMoment = {
  id: string;
  character: string;
  episode_id: string;
  type: "first_appearance" | "last_appearance" | "death";
  season: number;
  episode: number;
  title: string;
};

export type CharacterMomentsResponse = {
  moments: CharacterMoment[];
  total: number;
};

export type SeasonStats = {
  episode_count: number;
  characters: Record<string, number>;
  themes: string[];
  theme_counts: Record<string, number>;
};

export type SeasonComparisonResponse = {
  seasons: Record<string, SeasonStats>;
};

export async function fetchQuotes(
  character?: string,
  season?: number,
  search?: string
): Promise<QuotesResponse> {
  const params = new URLSearchParams();
  if (character) params.append("character", character);
  if (season) params.append("season", season.toString());
  if (search) params.append("search", search);

  const url = `${API_BASE}/reminiscence/quotes${params.toString() ? `?${params.toString()}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch quotes: ${res.status}`);
  return res.json();
}

export async function fetchCharacterMoments(character?: string): Promise<CharacterMomentsResponse> {
  const url = `${API_BASE}/reminiscence/character-moments${character ? `?character=${encodeURIComponent(character)}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch character moments: ${res.status}`);
  return res.json();
}

export async function fetchSeasonComparison(): Promise<SeasonComparisonResponse> {
  const res = await fetch(`${API_BASE}/reminiscence/season-comparison`);
  if (!res.ok) throw new Error(`Failed to fetch season comparison: ${res.status}`);
  return res.json();
}

