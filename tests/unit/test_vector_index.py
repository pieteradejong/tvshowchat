"""The brute-force cosine index: exact, deterministic, season-filterable."""
import json

import numpy as np
import pytest

from app.services import vector_store as vs
from app.services.storage.document_store import BuffyDocumentStore

# Four episodes on unit axes, so similarity to a query is easy to reason about.
EPISODES = {
    (1, "01"): [1.0, 0.0, 0.0],
    (1, "02"): [0.0, 1.0, 0.0],
    (2, "01"): [0.9, 0.1, 0.0],
    (2, "02"): [0.0, 0.0, 1.0],
}


class FakeEmbedder:
    """Maps known words to fixed vectors; never touches the network."""

    VOCAB = {"alpha": [1.0, 0.0, 0.0], "beta": [0.0, 1.0, 0.0], "gamma": [0.0, 0.0, 1.0]}

    def encode(self, text):
        return np.array(self.VOCAB.get(text, [0.0, 0.0, 0.0]))


@pytest.fixture
def store(tmp_path, monkeypatch):
    doc_store = BuffyDocumentStore(base_path=str(tmp_path))
    by_season: dict[int, dict] = {}
    for (season, ep), vec in EPISODES.items():
        by_season.setdefault(season, {})[ep] = (vec, f"S{season}E{ep}")
    for season, eps in by_season.items():
        (doc_store.episodes_path / f"season_{season}.json").write_text(json.dumps({
            ep: {"season_number": season, "episode_number": ep, "title": title,
                 "airdate": "", "summary": [f"summary of {title}"]}
            for ep, (_, title) in eps.items()
        }))
        (doc_store.embeddings_path / f"season_{season}_embeddings.json").write_text(json.dumps({
            ep: {"summary_embedding": vec} for ep, (vec, _) in eps.items()
        }))
    monkeypatch.setattr(vs, "load_embedder", FakeEmbedder)
    return vs.AdvancedVectorStore(doc_store)


def ids(hits):
    return [m["id"] for m, _ in hits]


def test_exact_nearest_order(store):
    hits = store._nearest(np.array([1.0, 0.0, 0.0]), 4, None)
    assert ids(hits) == ["s01e01", "s02e01", "s01e02", "s02e02"]
    assert hits[0][1] == pytest.approx(1.0)


def test_unnormalised_query_gives_same_cosine(store):
    a = store._nearest(np.array([1.0, 0.0, 0.0]), 4, None)
    b = store._nearest(np.array([7.0, 0.0, 0.0]), 4, None)
    assert ids(a) == ids(b)
    assert [s for _, s in a] == pytest.approx([s for _, s in b])


def test_season_filter(store):
    hits = store._nearest(np.array([1.0, 0.0, 0.0]), 10, 2)
    assert ids(hits) == ["s02e01", "s02e02"]


def test_n_caps_results(store):
    assert len(store._nearest(np.array([1.0, 0.0, 0.0]), 2, None)) == 2


def test_ties_break_by_index_order_deterministically(store):
    # Orthogonal to every episode except via the zero entries: all scores tie at 0.
    query = np.array([0.0, 0.0, 0.0])
    assert store._nearest(query, 4, None) == []  # zero query is rejected, not NaN
    tie = np.array([0.0, 0.0, -1.0])  # s01e01, s01e02, s02e01 all score 0
    first = ids(store._nearest(tie, 3, None))
    assert first == ["s01e01", "s01e02", "s02e01"]
    assert all(ids(store._nearest(tie, 3, None)) == first for _ in range(20))


def test_search_episodes_end_to_end(store):
    results = store.search_episodes("gamma", limit=1)
    assert [(r["season"], r["episode"]) for r in results] == [(2, "02")]
    assert set(results[0]) >= {"title", "score", "text", "snippets", "characters", "themes"}


def test_stats_count_indexed_episodes(store):
    stats = store.get_stats()
    assert stats["indexed_episodes"] == 4
    assert stats["total_episodes"] == 4
    assert "chromadb_episodes" not in stats


def test_rebuild_picks_up_new_data(store):
    store._ensure_index()
    season_file = store.document_store.episodes_path / "season_2.json"
    data = json.loads(season_file.read_text())
    del data["02"]
    season_file.write_text(json.dumps(data))
    assert store.rebuild_from_document_store()["indexed_episodes"] == 3


def test_chromadb_is_gone():
    import importlib.util

    assert importlib.util.find_spec("chromadb") is None
