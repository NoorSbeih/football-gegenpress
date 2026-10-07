from pathlib import Path

import pandas as pd
import pytest

from gegenpress.extract import cache_is_complete, extract_competition, normalize_frame


def _matches() -> pd.DataFrame:
    return pd.DataFrame({"match_id": [11, 12], "home_team": ["Canada", "England"]})


def _events(match_id: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_id": [match_id],
            "index": [1],
            "type": ["Pass"],
            "location": [[61.0, 40.1]],
            "counterpress": [True],
            "possession": [2],
            "possession_team": ["Morocco"],
            "tactics": [{"formation": 433}],
        }
    )


def test_second_extract_skips_http(tmp_path: Path) -> None:
    calls: list[tuple] = []

    def matches(competition_id: int, season_id: int) -> pd.DataFrame:
        calls.append(("matches", competition_id, season_id))
        return _matches()

    def events(match_id: int) -> pd.DataFrame:
        calls.append(("events", match_id))
        return _events(match_id)

    first = extract_competition(
        competition_key="wc2022",
        competition_id=43,
        season_id=106,
        root=tmp_path,
        matches_fetcher=matches,
        events_fetcher=events,
        workers=2,
    )
    assert first.from_cache is False
    assert first.event_http_fetches == 2
    assert ("matches", 43, 106) in calls

    calls.clear()
    second = extract_competition(
        competition_key="wc2022",
        competition_id=43,
        season_id=106,
        root=tmp_path,
        matches_fetcher=matches,
        events_fetcher=events,
    )
    assert calls == []
    assert second.from_cache is True
    assert second.match_count == 2
    assert cache_is_complete(tmp_path, "wc2022")


def test_partial_cache_fetches_only_missing_events(tmp_path: Path) -> None:
    extract_competition(
        competition_key="wc2022",
        competition_id=43,
        season_id=106,
        root=tmp_path,
        matches_fetcher=lambda *_: _matches(),
        events_fetcher=_events,
    )
    (tmp_path / "data" / "raw" / "wc2022" / "events" / "12.parquet").unlink()
    calls: list[int] = []

    def events(match_id: int) -> pd.DataFrame:
        calls.append(match_id)
        return _events(match_id)

    result = extract_competition(
        competition_key="wc2022",
        competition_id=43,
        season_id=106,
        root=tmp_path,
        matches_fetcher=lambda *_: pytest.fail("matches HTTP should not run"),
        events_fetcher=events,
    )
    assert calls == [12]
    assert result.matches_http is False
    assert result.event_http_fetches == 1


def test_normalize_frame_json_encodes_lists_and_keeps_bools() -> None:
    frame = normalize_frame(
        pd.DataFrame(
            {
                "location": [[61.0, 40.1], None],
                "tactics": [{"formation": 433}, None],
                "counterpress": [True, None],
            }
        )
    )
    assert frame.loc[0, "location"] == "[61.0, 40.1]"
    assert frame.loc[0, "tactics"] == '{"formation": 433}'
    assert bool(frame.loc[0, "counterpress"]) is True
    assert pd.isna(frame.loc[1, "counterpress"])
    assert str(frame["counterpress"].dtype) == "boolean"
