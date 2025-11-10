export interface SearchResult {
  season: number;
  episode: string;
  title: string;
  airdate: string;
  content_type: string;
  text: string;
  snippets?: string[];
  score: number;
  characters: string[];
  themes: string[];
  context: string;
}
