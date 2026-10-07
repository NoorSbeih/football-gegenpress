"""StatsBomb open data to a local parquet cache.

A second build reads the cache and does not call the network when every
match in ``matches.parquet`` already has an events file.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from gegenpress.config import events_dir, matches_path

EventFetcher = Callable[[int], pd.DataFrame]
MatchFetcher = Callable[[int, int], pd.DataFrame]


@dataclass(frozen=True)
class ExtractResult:
    match_count: int
    matches_http: bool
    event_http_fetches: int

    @property
    def from_cache(self) -> bool:
        return not self.matches_http and self.event_http_fetches == 0


class StatsBombClient:
    """Open-data client. No credentials."""

    def matches(self, competition_id: int, season_id: int) -> pd.DataFrame:
        from statsbombpy import sb

        _silence_open_data_warning()
        return sb.matches(competition_id=competition_id, season_id=season_id)

    def events(self, match_id: int) -> pd.DataFrame:
        from statsbombpy import sb

        _silence_open_data_warning()
        return sb.events(match_id=match_id)


def extract_competition(
    *,
    competition_key: str,
    competition_id: int,
    season_id: int,
    root: Path,
    matches_fetcher: MatchFetcher | None = None,
    events_fetcher: EventFetcher | None = None,
    workers: int = 6,
) -> ExtractResult:
    client = StatsBombClient()
    fetch_matches = matches_fetcher or client.matches
    fetch_events = events_fetcher or client.events

    matches_file = matches_path(root, competition_key)
    event_files = events_dir(root, competition_key)
    event_files.mkdir(parents=True, exist_ok=True)

    matches_http = False
    if matches_file.exists():
        matches = pd.read_parquet(matches_file)
    else:
        matches = fetch_matches(competition_id, season_id)
        matches_http = True
        _write_parquet(matches, matches_file)

    if "match_id" not in matches.columns:
        raise ValueError("matches parquet is missing match_id")

    match_ids = [int(match_id) for match_id in matches["match_id"].tolist()]
    missing = [
        match_id for match_id in match_ids if not _event_file(event_files, match_id).exists()
    ]
    if not missing:
        return ExtractResult(
            match_count=len(match_ids),
            matches_http=matches_http,
            event_http_fetches=0,
        )

    print(f"fetching {len(missing)} event files ({len(match_ids) - len(missing)} already cached)")
    _fetch_events(missing, event_files, fetch_events, workers)
    return ExtractResult(
        match_count=len(match_ids),
        matches_http=matches_http,
        event_http_fetches=len(missing),
    )


def cache_is_complete(root: Path, competition_key: str) -> bool:
    matches_file = matches_path(root, competition_key)
    if not matches_file.exists():
        return False
    matches = pd.read_parquet(matches_file)
    if matches.empty or "match_id" not in matches.columns:
        return False
    folder = events_dir(root, competition_key)
    return all(_event_file(folder, int(match_id)).exists() for match_id in matches["match_id"])


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Make a statsbombpy frame writable as parquet.

    Lists and dicts become JSON strings. Bool columns with missing values
    become pandas nullable booleans. ``location`` is therefore a string
    like ``[61.0, 40.1]``, not two numeric columns.
    """
    out = frame.copy()
    for column in out.columns:
        if out[column].dtype != object:
            continue
        out[column] = _normalize_object_column(out[column])
    return out


def _fetch_events(
    match_ids: list[int],
    folder: Path,
    fetch_events: EventFetcher,
    workers: int,
) -> None:
    workers = max(1, min(workers, len(match_ids)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_fetch_one, match_id, folder, fetch_events): match_id
            for match_id in match_ids
        }
        done = 0
        for future in as_completed(futures):
            future.result()
            done += 1
            print(f"events {done}/{len(match_ids)}", flush=True)


def _fetch_one(match_id: int, folder: Path, fetch_events: EventFetcher) -> None:
    destination = _event_file(folder, match_id)
    frame = fetch_events(match_id)
    if "match_id" not in frame.columns:
        frame = frame.copy()
        frame["match_id"] = match_id
    _write_parquet(frame, destination)


def _event_file(folder: Path, match_id: int) -> Path:
    return folder / f"{match_id}.parquet"


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".parquet.tmp")
    try:
        normalize_frame(frame).to_parquet(temporary, index=False)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _normalize_object_column(series: pd.Series) -> pd.Series:
    values = series.tolist()
    kinds = {_kind(value) for value in values if not _is_null(value)}
    if not kinds or kinds == {"str"}:
        return series.map(lambda value: None if _is_null(value) else str(value)).astype("string")
    if kinds == {"bool"}:
        return series.map(lambda value: None if _is_null(value) else bool(value)).astype("boolean")
    if kinds <= {"list", "dict"}:
        return series.map(_json_or_null).astype("string")
    return series.map(_mixed_cell).astype("string")


def _json_or_null(value: object) -> str | None:
    if _is_null(value):
        return None
    return json.dumps(value, default=_json_default)


def _mixed_cell(value: object) -> str | None:
    if _is_null(value):
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=_json_default)
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    return str(value)


def _kind(value: object) -> str:
    if isinstance(value, (bool, np.bool_)):
        return "bool"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, (list, tuple)):
        return "list"
    if isinstance(value, str):
        return "str"
    return "other"


def _is_null(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict, str, bytes, tuple)):
        return False
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(missing)


def _json_default(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot encode {type(value).__name__}")


def _silence_open_data_warning() -> None:
    from statsbombpy.api_client import NoAuthWarning

    warnings.filterwarnings("ignore", category=NoAuthWarning)
