"""Run the warehouse SQL in order. Full rebuild from raw tables."""

from dataclasses import dataclass
from pathlib import Path

import duckdb

from gegenpress.config import ROOT, database_path

SQL_FILES = (
    "staging/01_events.sql",
    "staging/02_possessions.sql",
    "staging/03_turnovers.sql",
    "marts/10_press_windows.sql",
    "marts/11_team_press.sql",
    "marts/12_pitch_bins.sql",
    "marts/13_match_turnovers.sql",
    "marts/14_regain_hist.sql",
)


@dataclass(frozen=True)
class TransformSummary:
    live_turnovers: int
    excluded_restarts: int
    regain_pct_5: float | None
    regain_pct_8: float | None
    counterpress_share: float | None
    exclude_reasons: tuple[tuple[str, int], ...]
    top_high_loss: tuple[tuple[str, int, float | None, int], ...]
    bottom_high_loss: tuple[tuple[str, int, float | None, int], ...]


def transform(
    competition_key: str,
    root: Path = ROOT,
    sql_root: Path | None = None,
) -> TransformSummary:
    if not competition_key.replace("_", "").isalnum():
        raise ValueError(f"unsafe competition key: {competition_key}")
    sql_dir = sql_root or (ROOT / "sql")
    database = database_path(root)
    connection = duckdb.connect(str(database))
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS staging")
        connection.execute("CREATE SCHEMA IF NOT EXISTS marts")
        connection.execute(
            "CREATE OR REPLACE TABLE staging.meta AS SELECT ?::VARCHAR AS competition_key",
            [competition_key],
        )
        for relative in SQL_FILES:
            script = (sql_dir / relative).read_text(encoding="utf-8")
            connection.execute(script)
        return _summarize(connection)
    finally:
        connection.close()


def _summarize(connection: duckdb.DuckDBPyConnection) -> TransformSummary:
    live, excluded, pct5, pct8, counter = connection.execute(
        """
        SELECT
            (SELECT count(*) FROM marts.press_windows),
            (SELECT count(*) FROM staging.turnovers WHERE excluded),
            (
                SELECT 100.0 * count(*) FILTER (WHERE regained_5) / nullif(count(*), 0)
                FROM marts.press_windows
            ),
            (
                SELECT 100.0 * count(*) FILTER (WHERE regained) / nullif(count(*), 0)
                FROM marts.press_windows
            ),
            (
                SELECT 100.0 * count(*) FILTER (WHERE statsbomb_counterpress)
                    / nullif(count(*), 0)
                FROM marts.press_windows
            )
        """
    ).fetchone()
    reasons = tuple(
        (str(reason), int(count))
        for reason, count in connection.execute(
            """
            SELECT exclude_reason, count(*)
            FROM staging.turnovers
            WHERE excluded
            GROUP BY exclude_reason
            ORDER BY count(*) DESC, exclude_reason
            """
        ).fetchall()
    )
    top = _ranked(connection, descending=True)
    bottom = _ranked(connection, descending=False)
    return TransformSummary(
        live_turnovers=int(live),
        excluded_restarts=int(excluded),
        regain_pct_5=None if pct5 is None else float(pct5),
        regain_pct_8=None if pct8 is None else float(pct8),
        counterpress_share=None if counter is None else float(counter),
        exclude_reasons=reasons,
        top_high_loss=top,
        bottom_high_loss=bottom,
    )


def _ranked(
    connection: duckdb.DuckDBPyConnection,
    *,
    descending: bool,
) -> tuple[tuple[str, int, float | None, int], ...]:
    direction = "DESC" if descending else "ASC"
    rows = connection.execute(
        f"""
        SELECT team, live_turnovers, high_loss_regain_pct, n_high
        FROM marts.team_press
        WHERE live_turnovers >= 40 AND high_loss_regain_pct IS NOT NULL
        ORDER BY high_loss_regain_pct {direction}, team
        LIMIT 5
        """
    ).fetchall()
    return tuple(
        (str(team), int(n), None if pct is None else float(pct), int(n_high))
        for team, n, pct, n_high in rows
    )


def format_summary(summary: TransformSummary) -> str:
    lines = [
        f"live turnovers: {summary.live_turnovers}",
        f"excluded restarts: {summary.excluded_restarts}",
        f"regain <=5s: {_pct(summary.regain_pct_5)}",
        f"regain <=8s: {_pct(summary.regain_pct_8)}",
        f"statsbomb counterpress share: {_pct(summary.counterpress_share)}",
        "excluded by reason:",
    ]
    for reason, count in summary.exclude_reasons:
        lines.append(f"  {reason}: {count}")
    lines.append("highest high-loss regain % (n>=40):")
    lines.extend(_rank_lines(summary.top_high_loss))
    lines.append("lowest high-loss regain % (n>=40):")
    lines.extend(_rank_lines(summary.bottom_high_loss))
    return "\n".join(lines)


def _rank_lines(rows: tuple[tuple[str, int, float | None, int], ...]) -> list[str]:
    if not rows:
        return ["  (none)"]
    return [
        f"  {team}: {_pct(pct)} on {n_high} high losses, {n} live turnovers"
        for team, n, pct, n_high in rows
    ]


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"
