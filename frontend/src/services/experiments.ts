import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface CharacterNode {
  id: string;
  name: string;
  episode_count: number;
  size: number;
}

export interface CharacterLink {
  source: string;
  target: string;
  value: number;
  strength: number;
}

export interface CharacterRelationships {
  nodes: CharacterNode[];
  links: CharacterLink[];
}

export interface ThemeCooccurrence {
  themes: string[];
  matrix: number[][];
  links: Array<{ source: string; target: string; value: number }>;
  episode_counts: Record<string, number>;
}

export interface EpisodeSimilarity {
  episodes: Array<{ id: string; season: number; episode: number; title: string }>;
  similarities: Array<{ source: string; target: string; similarity: number }>;
}

export interface CharacterJourney {
  nodes: Array<{ id: string; name: string; type: string; total_episodes?: number }>;
  links: Array<{ source: number; target: number; value: number }>;
}

export interface TemporalArc {
  timeline: Array<{
    id: string;
    season: number;
    episode: number;
    title: string;
    themes: string[];
    characters: Record<string, number>;
  }>;
}

export async function fetchCharacterRelationships(): Promise<CharacterRelationships> {
  const response = await axios.get(`${API_BASE}/api/experiments/character-relationships`);
  return response.data;
}

export async function fetchThemeCooccurrence(): Promise<ThemeCooccurrence> {
  const response = await axios.get(`${API_BASE}/api/experiments/theme-cooccurrence`);
  return response.data;
}

export async function fetchEpisodeSimilarity(): Promise<EpisodeSimilarity> {
  const response = await axios.get(`${API_BASE}/api/experiments/episode-similarity`);
  return response.data;
}

export async function fetchCharacterJourney(): Promise<CharacterJourney> {
  const response = await axios.get(`${API_BASE}/api/experiments/character-journey`);
  return response.data;
}

export async function fetchTemporalArcs(): Promise<TemporalArc> {
  const response = await axios.get(`${API_BASE}/api/experiments/temporal-arcs`);
  return response.data;
}


