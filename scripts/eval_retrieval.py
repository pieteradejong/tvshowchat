#!/usr/bin/env python3
"""Measure retrieval accuracy, so changes to search can be judged instead of guessed.

Semantic search quality is the point of this app, and until now there was no way
to tell whether a change helped. This builds an evaluation set with real ground
truth and scores a retrieval strategy against it.

Ground truth comes from two places:

1. **Episode titles** (144 free, unambiguous pairs). Searching an exact episode
   title should return that episode. It is a weak query in the sense that real
   users ask differently, but it is objective and it is the case the current
   index fails most obviously.
2. **Hand-written known-answer queries** describing memorable events, where the
   correct episode is not in dispute.

Strategies compared:

- `episode`  - one vector per episode, encoded from the whole joined summary.
               This is what ships today, and MiniLM's 256-token ceiling means
               ~85% of the median summary never reaches the index.
- `chunk`    - one vector per summary paragraph, prefixed with the episode
               title, scored max-over-chunks. Same model, same corpus; the only
               variable is how the text is cut up.

    ./venv/bin/python scripts/eval_retrieval.py

Metrics: Recall@1, Recall@5, Recall@10 and MRR over the ground-truth set.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "app" / "content" / "btvs_all_seasons.json"

# Retrieval models are not interchangeable at the API level: some are trained
# with an asymmetric query/passage convention and score far worse if the query
# instruction is omitted. Keep that convention next to the model name so a
# comparison never accidentally handicaps one of them.
MODELS: dict[str, dict] = {
    "minilm": {
        "id": "all-MiniLM-L6-v2",
        "query_prefix": "",
        "note": "ships today; 384-dim, 256-token window",
    },
    "bge-small": {
        "id": "BAAI/bge-small-en-v1.5",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "note": "384-dim (same index size as minilm), 512-token window",
    },
}
DEFAULT_MODELS = ["minilm", "bge-small"]

# Known-answer queries. Ground truth is the episode any Buffy viewer would name.
KNOWN_ANSWERS = [
    ("episode where Buffy dies",                        "s05e22"),
    ("the musical episode where everyone sings",        "s06e07"),
    ("Buffy and the gang sing and dance",               "s06e07"),
    ("Buffy sends Angel to hell",                       "s02e22"),
    ("Angel loses his soul after sleeping with Buffy",  "s02e13"),
    ("Xander becomes a hyena",                          "s01e06"),
    ("the episode with no talking, everyone loses their voice", "s04e10"),
    ("Buffy's mother dies of a brain aneurysm",         "s05e16"),
    ("Willow's girlfriend Tara is shot",                "s06e19"),
    ("Buffy fights the Master and drowns",              "s01e12"),
    ("Faith and Buffy swap bodies",                     "s04e16"),
    ("the mayor ascends into a giant snake demon",      "s03e22"),
    ("Buffy runs away to Los Angeles and works as a waitress", "s03e01"),
    ("Oz turns into a werewolf for the first time",     "s02e15"),
    ("Buffy gets telepathic powers and reads minds",    "s03e18"),
    ("Spike and Drusilla arrive in Sunnydale",          "s02e03"),
    ("Buffy is brought back from the dead by Willow",   "s06e01"),
    ("the demon that makes everyone's fears come true at a frat party", "s01e11"),
    ("Buffy's sister Dawn appears for the first time",  "s05e01"),
    ("Giles turns into a demon",                        "s04e12"),
]


def episode_id(season: int, ep: str | int) -> str:
    return f"s{int(season):02d}e{int(ep):02d}"


def load_corpus() -> list[dict]:
    with CONTENT.open(encoding="utf-8") as f:
        raw = json.load(f)
    episodes = []
    for season_key, eps in raw.items():
        season = int(season_key.split("_")[1])
        for ep_key, ep in eps.items():
            episodes.append({
                "id": episode_id(season, ep_key),
                "season": season,
                "episode": int(ep_key),
                "title": ep.get("episode_title") or "",
                "paragraphs": [p for p in (ep.get("episode_summary") or []) if p.strip()],
            })
    return sorted(episodes, key=lambda e: e["id"])


def build_ground_truth(episodes: list[dict]) -> list[tuple[str, str, str]]:
    """(kind, query, expected_episode_id)"""
    gt = [("title", e["title"], e["id"]) for e in episodes if e["title"]]
    by_id = {e["id"] for e in episodes}
    for q, eid in KNOWN_ANSWERS:
        if eid not in by_id:
            print(f"  warning: known-answer target {eid} not in corpus, skipping", file=sys.stderr)
            continue
        gt.append(("known", q, eid))
    return gt


def normalize(m: np.ndarray) -> np.ndarray:
    return m / np.clip(np.linalg.norm(m, axis=1, keepdims=True), 1e-12, None)


def build_episode_index(model, episodes: list[dict]):
    """One vector per episode from the whole joined summary - today's behaviour."""
    texts = [" ".join(e["paragraphs"]) for e in episodes]
    vecs = normalize(np.asarray(model.encode(texts, batch_size=32, show_progress_bar=False)))
    owners = [e["id"] for e in episodes]
    return vecs, owners


def build_chunk_index(model, episodes: list[dict]):
    """One vector per paragraph, each prefixed with the episode title."""
    texts, owners = [], []
    for e in episodes:
        for para in e["paragraphs"]:
            texts.append(f"{e['title']}. {para}" if e["title"] else para)
            owners.append(e["id"])
    vecs = normalize(np.asarray(model.encode(texts, batch_size=64, show_progress_bar=False)))
    return vecs, owners


def rank(query_vec: np.ndarray, vecs: np.ndarray, owners: list[str], k: int = 10) -> list[str]:
    """Score every vector, collapse to best-scoring chunk per episode, return top-k ids."""
    scores = vecs @ query_vec
    best: dict[str, float] = {}
    for owner, s in zip(owners, scores):
        if s > best.get(owner, -2.0):
            best[owner] = float(s)
    return [eid for eid, _ in sorted(best.items(), key=lambda kv: -kv[1])[:k]]


def evaluate(model, vecs, owners, ground_truth, query_prefix: str = "") -> dict:
    queries = [query_prefix + q for _, q, _ in ground_truth]
    qvecs = normalize(np.asarray(model.encode(queries, batch_size=64, show_progress_bar=False)))

    buckets: dict[str, list[int]] = {}
    for (kind, _, expected), qv in zip(ground_truth, qvecs):
        top = rank(qv, vecs, owners, k=10)
        pos = top.index(expected) + 1 if expected in top else 0
        buckets.setdefault(kind, []).append(pos)
        buckets.setdefault("all", []).append(pos)

    out = {}
    for kind, positions in buckets.items():
        n = len(positions)
        out[kind] = {
            "n": n,
            "R@1": sum(1 for p in positions if p == 1) / n,
            "R@5": sum(1 for p in positions if 1 <= p <= 5) / n,
            "R@10": sum(1 for p in positions if p >= 1) / n,
            "MRR": sum(1 / p for p in positions if p) / n,
        }
    return out


def fmt(name: str, res: dict) -> str:
    rows = []
    for kind in ("title", "known", "all"):
        if kind not in res:
            continue
        m = res[kind]
        rows.append(f"  {kind:6} n={m['n']:<4} "
                    f"R@1 {m['R@1']:6.1%}   R@5 {m['R@5']:6.1%}   "
                    f"R@10 {m['R@10']:6.1%}   MRR {m['MRR']:.3f}")
    return f"{name}\n" + "\n".join(rows)


def main() -> int:
    from sentence_transformers import SentenceTransformer

    wanted = sys.argv[1:] or DEFAULT_MODELS
    unknown = [w for w in wanted if w not in MODELS]
    if unknown:
        print(f"unknown model key(s): {', '.join(unknown)}")
        print(f"available: {', '.join(MODELS)}")
        return 2

    episodes = load_corpus()
    ground_truth = build_ground_truth(episodes)
    n_title = sum(1 for k, _, _ in ground_truth if k == "title")
    n_known = sum(1 for k, _, _ in ground_truth if k == "known")
    print(f"corpus: {len(episodes)} episodes")
    print(f"ground truth: {n_title} title queries + {n_known} known-answer queries")

    for key in wanted:
        spec = MODELS[key]
        model = SentenceTransformer(spec["id"])
        prefix = spec["query_prefix"]
        print(f"\n{'=' * 72}")
        print(f"{key}  ({spec['id']})")
        print(f"  {spec['note']}; max_seq_length={model.max_seq_length}; "
              f"query_prefix={'yes' if prefix else 'none'}")
        print("=" * 72)

        ep_vecs, ep_owners = build_episode_index(model, episodes)
        ch_vecs, ch_owners = build_chunk_index(model, episodes)
        print(f"index: {len(ep_owners)} episode vectors / {len(ch_owners)} chunk vectors "
              f"({ch_vecs.nbytes / 1024:.0f} KB float32)\n")

        print(fmt("A. episode-level, whole summary in one vector  [today's indexing]",
                  evaluate(model, ep_vecs, ep_owners, ground_truth, prefix)))
        print()
        print(fmt("B. chunk-level, one vector per paragraph + title prefix",
                  evaluate(model, ch_vecs, ch_owners, ground_truth, prefix)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
