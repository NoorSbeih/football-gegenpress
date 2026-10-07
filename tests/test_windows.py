import duckdb


def test_regain_three_seconds_after_the_loss(connection: duckdb.DuckDBPyConnection) -> None:
    regained, seconds, zone = connection.execute(
        """
        SELECT regained, time_to_regain_s, regain_zone
        FROM marts.press_windows
        WHERE match_id = 1
        """
    ).fetchone()
    assert regained is True
    assert seconds == 3
    assert zone == "middle"


def test_no_regain_when_the_opponent_keeps_it(connection: duckdb.DuckDBPyConnection) -> None:
    regained, seconds, pressed, pressure_s = connection.execute(
        """
        SELECT regained, time_to_regain_s, pressed, time_to_first_pressure_s
        FROM marts.press_windows
        WHERE match_id = 2
        """
    ).fetchone()
    assert regained is False
    assert seconds is None
    assert pressed is False
    assert pressure_s is None


def test_pressure_arrives_at_one_point_two_seconds(connection: duckdb.DuckDBPyConnection) -> None:
    pressed, seconds, counter, count = connection.execute(
        """
        SELECT pressed, time_to_first_pressure_s, statsbomb_counterpress, pressures_in_window
        FROM marts.press_windows
        WHERE match_id = 1
        """
    ).fetchone()
    assert pressed is True
    assert abs(seconds - 1.2) < 1e-6
    assert counter is True
    assert count == 1


def test_period_end_censors_without_a_fake_regain(connection: duckdb.DuckDBPyConnection) -> None:
    censored, regained, seconds = connection.execute(
        """
        SELECT censored_by_period, regained, time_to_regain_s
        FROM marts.press_windows
        WHERE match_id = 6
        """
    ).fetchone()
    assert censored is True
    assert regained is False
    assert seconds is None
