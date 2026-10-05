# Notices and attribution

This repository contains two kinds of material under two different licenses.

## Code — MIT

All source code is licensed under the MIT License. See [`LICENSE`](LICENSE).

Copyright (c) 2023 Pieter de Jong

## Episode content — CC BY-SA 3.0

The episode datasets are **not** covered by the MIT license above. They are derived
from the Buffyverse Wiki, whose text is published under the
[Creative Commons Attribution-ShareAlike 3.0 Unported licence](https://creativecommons.org/licenses/by-sa/3.0/),
and they remain under that licence.

| Dataset | Source | Licence |
|---|---|---|
| `app/content/btvs_all_seasons.json` | [Buffyverse Wiki](https://buffy.fandom.com/) — *Buffy the Vampire Slayer* episode pages | CC BY-SA 3.0 |

Everything generated from those files — the per-season splits under `app/data/episodes/`,
the derived datasets (`episodes.json`, `character_arcs.json`, `character_moments.json`,
`season_stats.json`, `grid_episodes.json`) and the embeddings under `app/data/embeddings/` —
is a derivative work and carries the same licence.

### What this means if you reuse this data

- **Attribute.** Credit the Buffyverse Wiki and link back to it, and indicate that changes
  were made (the text here has been extracted, cleaned and restructured).
- **Share alike.** If you distribute this data or anything derived from it, do so under
  CC BY-SA 3.0 or a compatible licence.
- The attribution has to reach the people using your application, not just sit in the
  repository — share-alike is about the recipient of the work.

Wiki text is authored by its contributors. *Buffy the Vampire Slayer* and all related names,
characters and marks are the property of their respective rights holders; nothing here is
affiliated with or endorsed by them. The datasets contain factual episode metadata and
descriptive summaries, held for research and non-commercial use.

## Model

Semantic search uses [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
published under the Apache License 2.0. Model weights are not committed to this repository.

## Adding a show

Each show under `app/shows/<slug>/` carries its own `ATTRIBUTION.md` recording where its
content came from and under what licence. Add one before adding a dataset — see
`docs/ADDING_A_SHOW.md`.
