import json
from pathlib import Path

from gegenpress.export import export


def test_export_writes_static_json(warehouse: Path) -> None:
    label = export("wc2022", warehouse)
    data_root = warehouse / "web" / "public" / "data"
    competitions = json.loads((data_root / "competitions.json").read_text(encoding="utf-8"))
    teams = json.loads((data_root / "teams" / "wc2022.json").read_text(encoding="utf-8"))
    assert competitions["competitions"][0]["default_match_label"] == label
    high = next(team for team in teams["teams"] if team["team"] == "HighSide")
    assert high["high_loss_regain_pct"] == 50
    assert high["sufficient"] is False
    pitch_path = data_root / "pitches" / f"{high['team_id']}.json"
    pitch = json.loads(pitch_path.read_text(encoding="utf-8"))
    assert pitch["bins"]
    match = json.loads((data_root / "matches" / "1.json").read_text(encoding="utf-8"))
    assert match["turnovers"][0]["regained"] is True
