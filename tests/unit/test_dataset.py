"""The tracked dataset is the source everything else is built from."""
import json

import pytest

from tests.conftest import ROOT

CONTENT = ROOT / "app" / "content" / "btvs_all_seasons.json"
EPISODES_PER_SEASON = {1: 12, 2: 22, 3: 22, 4: 22, 5: 22, 6: 22, 7: 22}
EMBEDDING_DIM = 384


@pytest.fixture(scope="module")
def data():
    with CONTENT.open(encoding="utf-8") as f:
        return json.load(f)


def test_all_seven_seasons(data):
    assert set(data) == {f"season_{n}" for n in EPISODES_PER_SEASON}


@pytest.mark.parametrize("season,count", EPISODES_PER_SEASON.items())
def test_episode_numbers_are_complete(data, season, count):
    assert set(data[f"season_{season}"]) == {f"{i:02}" for i in range(1, count + 1)}


def test_144_episodes(data):
    assert sum(len(eps) for eps in data.values()) == 144


def test_required_fields_have_the_right_types(data):
    for season in data.values():
        for key, ep in season.items():
            assert ep["episode_number"] == key
            assert isinstance(ep["episode_title"], str) and ep["episode_title"]
            assert isinstance(ep["episode_airdate"], str)
            assert isinstance(ep["episode_summary"], list)
            # The crawler never fills synopsis; summary is the searchable text.
            assert ep["episode_synopsis"] is None or isinstance(ep["episode_synopsis"], list)


def test_summary_embeddings_are_384_dim_where_present(data):
    with_embedding = 0
    for season in data.values():
        for ep in season.values():
            vec = ep.get("summary_embedding")
            if vec is not None:
                assert len(vec) == EMBEDDING_DIM
                with_embedding += 1
    # Every episode with a summary is searchable only if it has a vector.
    with_summary = sum(1 for s in data.values() for e in s.values() if e["episode_summary"])
    assert with_embedding >= with_summary
