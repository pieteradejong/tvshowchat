# Buffy Series Visualization Roadmap

This document captures the phased plan for the series visualization.

## v1 (simple, polished)
- Episode Timeline (seasons stacked): hover logline, click selects episode.
- Character Arc Sparklines (top 6–8 chars): presence score per episode; highlight selected/hovered episode.
- Episode Detail Card: title, airdate, logline, top themes.
- Data: precomputed JSON bundles
  - `app/data/episodes/episodes.json`
  - `app/data/episodes/character_arcs.json`
- Backend endpoints
  - `GET /api/series/episodes`
  - `GET /api/series/character-arcs`
- Frontend components
  - `frontend/src/components/SeriesTimeline.tsx`
  - `frontend/src/components/CharacterSparklines.tsx`
  - `frontend/src/components/EpisodeDetailCard.tsx`
  - integrated via `frontend/src/components/SeriesVis.tsx` and tab in `App.tsx`
- Acceptance
  - Hover/select updates sparklines and detail card
  - Fast load (<1s UI; data <2MB), responsive, keyboard-focusable timeline buttons

## v2 (medium richness)
- Compare Characters (pin 2–4) overlay in sparklines.
- Theme Heatmap (themes × episodes) with cross-highlighting.
- Relationship Graph per season with time slider.
- Episode similarity endpoint and carousel (embeddings).
- Backend: `/api/themes/heatmap`, `/api/relationships/season/:s`, `/api/episodes/:id/similar`.
- Data: BERTopic themes, co-appearance graph, embedding matrix + kNN.

## v3 (heavy authoring & sharing)
- Story Builder (drag episodes; export/share view state/PNG/MP4).
- Natural-language query to surface episodes/arcs.
- Beat/tension annotations and overlays.
- Session persistence and shareable links.

## Data notes
- Presence score (v1): counts of character name mentions in episode summaries (approx).
- Themes (v1): top keyword frequency with stopword filtering.
- Future: add sentiment curves, scene segmentation, curated theme taxonomy, relation extraction.


