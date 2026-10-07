"""Load the parquet cache into DuckDB raw tables. Full rebuild, no HTTP."""

from dataclasses import dataclass
from pathlib import Path

import duckdb

from gegenpress.config import database_path, events_dir, matches_path


@dataclass(frozen=True)
class LoadResult:
    match_count: int
    event_count: int
    database: Path


def load_raw(competition_key: str, root: Path) -> LoadResult:
    matches_file = matches_path(root, competition_key)
    event_folder = events_dir(root, competition_key)
    if not matches_file.exists():
        raise FileNotFoundError(f"missing matches cache: {matches_file}")
    event_files = sorted(event_folder.glob("*.parquet"))
    if not event_files:
        raise FileNotFoundError(f"missing event cache: {event_folder}")

    database = database_path(root)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database))
    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        matches_sql = _sql_path(matches_file)
        events_sql = _sql_path(event_folder / "*.parquet")
        connection.execute(
            f"CREATE OR REPLACE TABLE raw.matches AS SELECT * FROM read_parquet('{matches_sql}')"
        )
        connection.execute(
            "CREATE OR REPLACE TABLE raw.events AS "
            f"SELECT * FROM read_parquet('{events_sql}', union_by_name=true)"
        )
        match_count = connection.execute("SELECT count(*) FROM raw.matches").fetchone()[0]
        event_count = connection.execute("SELECT count(*) FROM raw.events").fetchone()[0]
    finally:
        connection.close()
    return LoadResult(
        match_count=int(match_count),
        event_count=int(event_count),
        database=database,
    )


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")
