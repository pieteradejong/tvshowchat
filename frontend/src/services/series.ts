export type EpisodeLite = {
  id: string;
  season: number;
  episode: number;
  title: string;
  airdate: string;
  logline: string;
  themes: string[];
};

export type CharacterArcPoint = { episode_id: string; presence_score: number };
export type CharacterArcs = Record<string, CharacterArcPoint[]>;

const API_BASE = "/api";

export async function fetchEpisodes(): Promise<EpisodeLite[]> {
  const res = await fetch(`${API_BASE}/series/episodes`);
  if (!res.ok) throw new Error(`Failed to fetch episodes: ${res.status}`);
  return res.json();
}

export async function fetchCharacterArcs(): Promise<CharacterArcs> {
  const res = await fetch(`${API_BASE}/series/character-arcs`);
  if (!res.ok) throw new Error(`Failed to fetch character arcs: ${res.status}`);
  return res.json();
}


