import pytest
import os
import glob
import json


@pytest.fixture(scope="module")
def json_data():
    file_list = glob.glob("buffy_all_seasons_*.json")
    file_list.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    most_recent_file = file_list[0]
    with open(most_recent_file, "r") as f:
        return json.load(f)


def test_json_contains_all_seasons(json_data):
    expected_keys = [f"season_{i}" for i in range(1, 8)]
    assert set(json_data.keys()) == set(expected_keys)


def test_json_contains_all_episodes(json_data):
    # hardcode aspects of the data; verify data completeness and
    # keep meta data close to analysis for context
    SEASON_ONE_EPISODES = 12
    SEASON_TWO_THRU_SEVEN_EPISODES = 22
    expected_s1_episode_numbers = set(
        [f"{i:02}" for i in range(1, SEASON_ONE_EPISODES + 1)]
    )
    expected_s2_thru_7_episode_numbers = set(
        [f"{i:02}" for i in range(1, SEASON_TWO_THRU_SEVEN_EPISODES + 1)]
    )

    season_keys = [f"season_{i}" for i in range(1, 8)]

    assert set(json_data[season_keys[0]].keys()) == expected_s1_episode_numbers
    for sk in season_keys[1:]:
        assert set(json_data[sk].keys()) == expected_s2_thru_7_episode_numbers


def test_json_all_episodes_contain_correct_metadata(json_data):
    season_keys = [f"season_{i}" for i in range(1, 8)]
    for season_key in season_keys:
        for episode_key in json_data[season_key]:
            episode_data = json_data[season_key][episode_key]
            assert isinstance(episode_data["episode_number"], str)
            assert isinstance(episode_data["episode_airdate"], str)
            assert isinstance(episode_data["episode_title"], str)
            assert isinstance(episode_data["episode_synopsis"], list)
            assert isinstance(episode_data["episode_summary"], list)

            # These two assertions would be valuable, but cannot be guaranteed
            # for all episodes, showing the limits of data integrity checks.
            # For example, Season 4 Episode 22 contains neither synopsis not summary.
            # assert len(episode_data['episode_synopsis']) > 0
            # assert len(episode_data['episode_summary']) > 0
