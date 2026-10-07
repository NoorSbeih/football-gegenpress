"""Write marts to the JSON files the static site reads."""

import json
from decimal import Decimal
from pathlib import Path

import duckdb

from gegenpress.config import ROOT, database_path, get_competition

PERCENT_KEYS = {
    "regain_pct_5",
    "regain_pct_8",
    "pressure_pct_8",
    "high_turnover_share",
    "high_loss_regain_pct",
    "low_loss_regain_pct",
    "counterpress_share",
    "mean_regain_x",
}
SECOND_KEYS = {
    "median_time_to_regain_8",
    "median_time_to_pressure_8",
    "time_to_regain_s",
    "time_to_first_pressure_s",
    "time_to_regain_5_s",
    "loss_x",
    "loss_y",
    "regain_x",
    "regain_y",
}


def export(competition_key: str, root: Path = ROOT) -> str:
    spec = get_competition(competition_key)
    connection = duckdb.connect(str(database_path(root)), read_only=True)
    try:
        teams = _rows(
            connection,
            """
            SELECT
                team_id, team, competition, live_turnovers, excluded_restarts,
                regain_pct_5, regain_pct_8, median_time_to_regain_8,
                pressure_pct_8, median_time_to_pressure_8, high_turnover_share,
                n_high, n_low, high_loss_regain_pct, low_loss_regain_pct,
                mean_regain_x, counterpress_share, n_regained_8
            FROM marts.team_press
            ORDER BY high_loss_regain_pct DESC NULLS LAST, team
            """,
        )
        for team in teams:
            team["sufficient"] = int(team["live_turnovers"]) >= 40
        bins = _rows(
            connection,
            """
            SELECT team_id, layer, window_s, bx, bin_y, n
            FROM marts.pitch_bins
            ORDER BY team_id, layer, window_s, bx, bin_y
            """,
        )
        hist = _rows(
            connection,
            """
            SELECT team_id, window_s, bucket, n
            FROM marts.regain_hist
            ORDER BY team_id, window_s, bucket
            """,
        )
        featured = _featured(connection)
        match_rows = _rows(
            connection,
            """
            SELECT *
            FROM marts.match_turnovers
            ORDER BY match_id, period, loss_minute, loss_second, loss_index
            """,
        )
        catalog = _rows(
            connection,
            """
            SELECT
                match_id, match_date, competition_stage, home_team, away_team,
                home_team_id, away_team_id, home_score, away_score
            FROM raw.matches
            ORDER BY match_date, match_id
            """,
        )
        rates = _rows(
            connection,
            """
            SELECT
                100.0 * count(*) FILTER (WHERE regained_5) / count(*) AS regain_pct_5,
                100.0 * count(*) FILTER (WHERE regained) / count(*) AS regain_pct_8,
                100.0 * count(*) FILTER (WHERE pressed) / count(*) AS pressure_pct_8,
                100.0 * count(*) FILTER (WHERE statsbomb_counterpress) / count(*)
                    AS counterpress_share,
                count(*) AS live_turnovers
            FROM marts.press_windows
            """,
        )[0]
        excluded = connection.execute(
            """
            SELECT
                count(*) FILTER (WHERE exclude_reason != 'no_on_ball_event'),
                count(*) FILTER (WHERE exclude_reason = 'no_on_ball_event')
            FROM staging.turnovers
            WHERE excluded
            """
        ).fetchone()
    finally:
        connection.close()

    data_root = root / "web" / "public" / "data"
    _write_pitches(data_root / "pitches", teams, bins, hist)
    match_index = _write_matches(data_root / "matches", match_rows, catalog)
    _dump(
        data_root / "teams" / f"{competition_key}.json",
        {"competition": competition_key, "teams": teams},
    )
    label = _label(featured)
    _dump(
        data_root / "competitions.json",
        {
            "competitions": [
                {
                    "key": spec.key,
                    "name": spec.name,
                    "competition_id": spec.competition_id,
                    "season_id": spec.season_id,
                    "live_turnovers": rates["live_turnovers"],
                    "excluded_restarts": int(excluded[0]),
                    "unlocated": int(excluded[1]),
                    "regain_pct_5": rates["regain_pct_5"],
                    "regain_pct_8": rates["regain_pct_8"],
                    "pressure_pct_8": rates["pressure_pct_8"],
                    "counterpress_share": rates["counterpress_share"],
                    "default_match_id": featured["match_id"],
                    "default_match_label": label,
                }
            ]
        },
    )
    _dump(data_root / "matches" / "index.json", match_index)
    return label


def _featured(connection: duckdb.DuckDBPyConnection) -> dict:
    rows = _rows(
        connection,
        """
        WITH top AS (
            SELECT team_id
            FROM marts.team_press
            ORDER BY
                (live_turnovers >= 40) DESC,
                high_loss_regain_pct DESC NULLS LAST,
                live_turnovers DESC
            LIMIT 1
        ),
        counts AS (
            SELECT w.match_id, count(*) AS n
            FROM marts.press_windows AS w
            INNER JOIN top AS t
                ON w.losing_team_id = t.team_id
                OR w.winning_team_id = t.team_id
            GROUP BY w.match_id
        )
        SELECT
            c.match_id,
            m.match_date,
            m.home_team,
            m.away_team,
            m.home_score,
            m.away_score,
            m.competition_stage
        FROM counts AS c
        INNER JOIN raw.matches AS m ON m.match_id = c.match_id
        ORDER BY c.n DESC, m.match_date, c.match_id
        LIMIT 1
        """,
    )
    return rows[0]


def _write_pitches(
    folder: Path,
    teams: list[dict],
    bins: list[dict],
    hist: list[dict],
) -> None:
    by_team_bins: dict[int, list[dict]] = {}
    by_team_hist: dict[int, list[dict]] = {}
    for cell in bins:
        by_team_bins.setdefault(int(cell["team_id"]), []).append(
            {key: value for key, value in cell.items() if key != "team_id"}
        )
    for bucket in hist:
        by_team_hist.setdefault(int(bucket["team_id"]), []).append(
            {key: value for key, value in bucket.items() if key != "team_id"}
        )
    for team in teams:
        team_id = int(team["team_id"])
        _dump(
            folder / f"{team_id}.json",
            {
                "team_id": team_id,
                "team": team["team"],
                "bins": by_team_bins.get(team_id, []),
                "histogram": by_team_hist.get(team_id, []),
            },
        )


def _write_matches(folder: Path, rows: list[dict], catalog: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(int(row["match_id"]), []).append(_turnover(row))
    index: list[dict] = []
    for match in catalog:
        match_id = int(match["match_id"])
        label = _score_label(match)
        payload = {
            "match_id": match_id,
            "date": match["match_date"],
            "stage": match["competition_stage"],
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "home_team_id": match["home_team_id"],
            "away_team_id": match["away_team_id"],
            "home_score": match["home_score"],
            "away_score": match["away_score"],
            "label": label,
            "turnovers": grouped.get(match_id, []),
        }
        _dump(folder / f"{match_id}.json", payload)
        index.append(
            {
                "match_id": match_id,
                "date": match["match_date"],
                "stage": match["competition_stage"],
                "label": label,
                "home_team_id": match["home_team_id"],
                "away_team_id": match["away_team_id"],
            }
        )
    return index


def _turnover(row: dict) -> dict:
    return {
        "period": row["period"],
        "minute": row["loss_minute"],
        "second": row["loss_second"],
        "team": row["losing_team"],
        "team_id": row["losing_team_id"],
        "zone": row["loss_zone"],
        "regained": row["regained"],
        "time_to_regain_s": row["time_to_regain_s"],
        "pressed": row["pressed"],
        "time_to_pressure_s": row["time_to_first_pressure_s"],
        "censored": row["censored_by_period"],
        "loss_x": row["loss_x"],
        "loss_y": row["loss_y"],
        "regain_x": row["regain_x"],
        "regain_y": row["regain_y"],
    }


def _score_label(match: dict) -> str:
    return f"{match['home_team']} {match['home_score']}–{match['away_score']} {match['away_team']}"


def _label(match: dict) -> str:
    return _score_label(match)


def _rows(connection: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = connection.execute(sql)
    columns = [item[0] for item in cursor.description]
    cleaned = []
    for row in cursor.fetchall():
        cleaned.append({key: _clean(key, value) for key, value in zip(columns, row)})
    return cleaned


def _clean(key: str, value: object) -> object:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        if key in PERCENT_KEYS or key.endswith("_pct") or key.endswith("_share"):
            return round(value, 1)
        if key in SECOND_KEYS or key.endswith("_s") or key.endswith("_x") or key.endswith("_y"):
            return round(value, 2)
        return round(value, 2)
    if isinstance(value, int):
        return value
    return value


def _dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
