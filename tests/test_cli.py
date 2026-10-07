import pytest

from gegenpress.cli import main


def test_build_is_not_implemented_yet() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["build", "--competition", "wc2022"])
    assert exc.value.code == 1


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert "gegenpress" in captured.out
