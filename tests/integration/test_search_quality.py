"""Search behaviour that must not change by accident.

The ranking baseline is the regression net for refactors and dependency
upgrades (see docs/SEARCH_ACCURACY.md). Re-record it only for a deliberate
change: ./venv/bin/python scripts/capture_search_baseline.py capture
"""
import json
import subprocess
import sys

import numpy as np
import pytest

from tests.conftest import ROOT

pytestmark = pytest.mark.model


def test_rankings_match_the_recorded_baseline():
    proc = subprocess.run(
        [sys.executable, "scripts/capture_search_baseline.py", "verify"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, proc.stdout[-3000:]


def test_query_model_matches_the_model_that_built_the_corpus():
    """Stored vectors and query vectors must come from the same model.

    The corpus vectors were built from the first 256 tokens of each summary.
    If a dependency upgrade or model change shifts the embedding space,
    every query silently degrades; this catches it.
    """
    from app.services.embedder import load_embedder

    data = json.loads((ROOT / "app/content/btvs_all_seasons.json").read_text(encoding="utf-8"))
    model = load_embedder()
    for season, ep in [("season_1", "01"), ("season_3", "22"), ("season_5", "22"), ("season_7", "22")]:
        episode = data[season][ep]
        stored = np.array(episode["summary_embedding"])
        fresh = model.encode(" ".join(episode["episode_summary"]))
        cos = float(stored @ fresh / (np.linalg.norm(stored) * np.linalg.norm(fresh)))
        assert cos > 0.999, f"{season}/{ep}: cosine {cos:.5f}"
