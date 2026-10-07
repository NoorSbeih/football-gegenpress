"""Competition config and on-disk paths."""

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "competitions.yaml"


class ConfigError(Exception):
    """Raised when a competition key is missing or incomplete."""


@dataclass(frozen=True)
class Competition:
    key: str
    name: str
    competition_id: int
    season_id: int


def get_competition(key: str, config_path: Path = CONFIG_PATH) -> Competition:
    with config_path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle) or {}
    competitions = document.get("competitions") or {}
    raw = competitions.get(key)
    if not isinstance(raw, dict):
        known = ", ".join(sorted(competitions)) or "(none)"
        raise ConfigError(f"Unknown competition {key!r}. Known keys: {known}")
    competition_id = raw.get("competition_id")
    season_id = raw.get("season_id")
    if competition_id is None or season_id is None:
        raise ConfigError(f"Competition {key!r} is missing competition_id or season_id")
    name = raw.get("name") or key
    return Competition(
        key=key,
        name=str(name),
        competition_id=int(competition_id),
        season_id=int(season_id),
    )


def raw_dir(root: Path, competition_key: str) -> Path:
    return root / "data" / "raw" / competition_key


def matches_path(root: Path, competition_key: str) -> Path:
    return raw_dir(root, competition_key) / "matches.parquet"


def events_dir(root: Path, competition_key: str) -> Path:
    return raw_dir(root, competition_key) / "events"


def database_path(root: Path) -> Path:
    return root / "data" / "gegenpress.duckdb"
