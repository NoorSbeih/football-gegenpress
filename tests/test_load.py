from pathlib import Path

import duckdb

from gegenpress.extract import extract_competition
from gegenpress.load import load_raw


def test_load_raw_counts_matches_and_events(tmp_path: Path) -> None:
    matches = {
        "match_id": [11, 12],
        "home_team": ["Canada", "England"],
        "away_team": ["Morocco", "Iran"],
    }

    def events(match_id: int):
        import pandas as pd

        return pd.DataFrame(
            {
                "match_id": [match_id, match_id],
                "index": [1, 2],
                "type": ["Pass", "Pressure"],
                "location": [[10.0, 20.0], [30.0, 40.0]],
                "counterpress": [None, True],
                "possession_team": ["Canada", "Morocco"],
            }
        )

    import pandas as pd

    extract_competition(
        competition_key="wc2022",
        competition_id=43,
        season_id=106,
        root=tmp_path,
        matches_fetcher=lambda *_: pd.DataFrame(matches),
        events_fetcher=events,
    )
    loaded = load_raw("wc2022", tmp_path)
    assert loaded.match_count == 2
    assert loaded.event_count == 4

    connection = duckdb.connect(str(loaded.database))
    try:
        location = connection.execute(
            "SELECT location FROM raw.events WHERE type = 'Pass' AND match_id = 11"
        ).fetchone()[0]
        pressed = connection.execute(
            "SELECT counterpress FROM raw.events WHERE type = 'Pressure' LIMIT 1"
        ).fetchone()[0]
    finally:
        connection.close()
    assert location == "[10.0, 20.0]"
    assert pressed is True
