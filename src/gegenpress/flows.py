"""Prefect flow: extract the parquet cache, then load DuckDB raw tables."""

from pathlib import Path

from prefect import flow, task

from gegenpress.config import ROOT, ConfigError, get_competition
from gegenpress.export import export
from gegenpress.extract import extract_competition
from gegenpress.load import load_raw
from gegenpress.transform import format_summary, transform


@task(name="extract")
def extract_task(competition_key: str, competition_id: int, season_id: int) -> dict:
    result = extract_competition(
        competition_key=competition_key,
        competition_id=competition_id,
        season_id=season_id,
        root=ROOT,
    )
    return {
        "match_count": result.match_count,
        "matches_http": result.matches_http,
        "event_http_fetches": result.event_http_fetches,
        "from_cache": result.from_cache,
    }


@task(name="load")
def load_task(competition_key: str) -> dict:
    result = load_raw(competition_key, ROOT)
    relative = result.database
    try:
        relative = result.database.relative_to(ROOT)
    except ValueError:
        relative = result.database
    return {
        "match_count": result.match_count,
        "event_count": result.event_count,
        "database": Path(relative).as_posix(),
    }


@task(name="transform")
def transform_task(competition_key: str) -> dict:
    summary = transform(competition_key, ROOT)
    print(format_summary(summary))
    return {
        "live_turnovers": summary.live_turnovers,
        "excluded_restarts": summary.excluded_restarts,
        "regain_pct_8": summary.regain_pct_8,
    }


@task(name="export")
def export_task(competition_key: str) -> str:
    return export(competition_key, ROOT)


@flow(name="gegenpress-build")
def build_flow(competition: str = "wc2022") -> None:
    try:
        spec = get_competition(competition)
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc
    extracted = extract_task(spec.key, spec.competition_id, spec.season_id)
    loaded = load_task(spec.key)
    cache = "cache hit, skipped HTTP" if extracted["from_cache"] else "fetched from StatsBomb"
    print(
        f"competition: {spec.key} ({spec.name}, id {spec.competition_id}, season {spec.season_id})"
    )
    print(
        f"extract: {cache}, {extracted['match_count']} matches, "
        f"{extracted['event_http_fetches']} event HTTP requests"
    )
    print(f"raw.matches: {loaded['match_count']}")
    print(f"raw.events: {loaded['event_count']}")
    print(f"duckdb: {loaded['database']}")
    transformed = transform_task(spec.key)
    featured = export_task(spec.key)
    print(
        f"windows: {transformed['live_turnovers']} live, "
        f"regain <=8s {_fmt_pct(transformed['regain_pct_8'])}"
    )
    print(f"match tape: {featured}")


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"
