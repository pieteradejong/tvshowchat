#!/usr/bin/env python3
"""Capture or verify a search-ranking baseline.

The lightweight-engine rewrite replaces ChromaDB + a locally-hosted
SentenceTransformer with a pluggable query embedder and a brute-force cosine
over precomputed vectors. The scoring, boosting and snippet-selection pipeline
is meant to survive that change untouched, and there is currently no test that
would notice if it didn't.

So: record what the engine returns today, then assert the same thing after.

    ./venv/bin/python scripts/capture_search_baseline.py capture
    ./venv/bin/python scripts/capture_search_baseline.py verify

`capture` writes tests/fixtures/search_baseline.json. `verify` re-runs the same
queries against whatever engine is currently wired up and reports any drift in
the ranked episode ids, exiting non-zero if the ordering changed.

Run `capture` against the *old* engine and `verify` against the new one while
both use the same embedding model; changing the engine and the model at the
same time makes a regression impossible to attribute.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QUERIES_FILE = ROOT / "tests" / "fixtures" / "search_queries.json"
BASELINE_FILE = ROOT / "tests" / "fixtures" / "search_baseline.json"

TOP_N = 5


def _load_queries() -> dict:
    with QUERIES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _run_all() -> dict:
    """Run every fixture query through the live search path."""
    # Imported lazily: this pulls in torch/chromadb on the pre-rewrite engine.
    from app.api.routes.search import _enhance_memory_query
    from app.services.vector_store import get_vector_store

    store = get_vector_store()
    spec = _load_queries()
    results: dict[str, list[dict]] = {}

    def record(key: str, query: str, season: int | None) -> None:
        hits = store.search_episodes(
            query=_enhance_memory_query(query), limit=TOP_N, season=season
        )
        results[key] = [
            {
                "id": f"s{h['season']:02d}e{int(h['episode']):02d}",
                "season": h["season"],
                "episode": h["episode"],
                "title": h["title"],
                # Rounded: float noise across numpy/pure-Python paths is not a regression.
                "score": round(float(h["score"]), 4),
                "content_type": h.get("content_type"),
                "characters": h.get("characters", []),
                "themes": h.get("themes", []),
            }
            for h in hits
        ]
        print(f"  {key}: {' '.join(r['id'] for r in results[key]) or '(no results)'}")

    print(f"Running {len(spec['queries'])} queries...")
    for item in spec["queries"]:
        record(item["q"], item["q"], None)

    print(f"Running {len(spec['season_filtered'])} season-filtered queries...")
    for item in spec["season_filtered"]:
        key = f"{item['q']} [s{item['season']}]"
        record(key, item["q"], item["season"])

    return results


def capture() -> int:
    results = _run_all()
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with BASELINE_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")
    total = sum(len(v) for v in results.values())
    print(f"\nWrote {BASELINE_FILE.relative_to(ROOT)} "
          f"({len(results)} queries, {total} ranked results)")
    return 0


def verify() -> int:
    if not BASELINE_FILE.exists():
        print(f"No baseline at {BASELINE_FILE.relative_to(ROOT)}; run `capture` first.")
        return 2

    with BASELINE_FILE.open(encoding="utf-8") as f:
        baseline = json.load(f)
    current = _run_all()

    drift: list[str] = []
    for key, expected in baseline.items():
        got = current.get(key)
        if got is None:
            drift.append(f"{key}: missing from current run")
            continue
        exp_ids = [r["id"] for r in expected]
        got_ids = [r["id"] for r in got]
        if exp_ids != got_ids:
            drift.append(f"{key}\n    was: {' '.join(exp_ids) or '(none)'}"
                         f"\n    now: {' '.join(got_ids) or '(none)'}")
    for key in current.keys() - baseline.keys():
        drift.append(f"{key}: present now, absent from baseline")

    print()
    if drift:
        print(f"RANKING DRIFT in {len(drift)} of {len(baseline)} queries:\n")
        for d in drift:
            print(f"  {d}")
        return 1
    print(f"OK - all {len(baseline)} queries return identical top-{TOP_N} rankings.")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if cmd not in {"capture", "verify"}:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(capture() if cmd == "capture" else verify())
