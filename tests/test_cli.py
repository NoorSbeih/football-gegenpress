import pytest

from gegenpress.cli import main


def test_build_runs_the_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_flow(competition: str) -> None:
        seen["competition"] = competition

    monkeypatch.setattr("gegenpress.flows.build_flow", fake_flow)
    main(["build", "--competition", "wc2022"])
    assert seen == {"competition": "wc2022"}


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert "gegenpress" in captured.out
