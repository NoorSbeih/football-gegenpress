import duckdb


def _one(connection: duckdb.DuckDBPyConnection, sql: str, params: list | None = None):
    return connection.execute(sql, params or []).fetchone()


def test_incomplete_pass_opens_one_turnover(connection: duckdb.DuckDBPyConnection) -> None:
    row = _one(
        connection,
        """
        SELECT loss_type, loss_x, loss_y, excluded, exclude_reason, losing_team
        FROM staging.turnovers
        WHERE match_id = 1
        """,
    )
    assert row[0] == "Pass"
    assert row[1] == 70
    assert row[2] == 40
    assert row[3] is False
    assert row[4] is None
    assert row[5] == "Pressers"


def test_restarts_are_excluded(connection: duckdb.DuckDBPyConnection) -> None:
    reasons = dict(
        connection.execute(
            """
            SELECT match_id, exclude_reason
            FROM staging.turnovers
            WHERE match_id IN (3, 4, 9, 10)
            """
        ).fetchall()
    )
    assert reasons == {3: "goal_kick", 4: "corner", 9: "penalty", 10: "drop_ball"}
    windows = _one(
        connection,
        "SELECT count(*) FROM marts.press_windows WHERE match_id IN (3, 4, 9, 10)",
    )
    assert windows[0] == 0


def test_shootout_creates_no_turnovers(connection: duckdb.DuckDBPyConnection) -> None:
    count = _one(connection, "SELECT count(*) FROM staging.turnovers WHERE match_id = 5")
    assert count[0] == 0


def test_same_team_possession_split_is_not_a_turnover(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    rows = connection.execute(
        """
        SELECT loss_type, loss_x, loss_y, excluded
        FROM staging.turnovers
        WHERE match_id = 8
        """
    ).fetchall()
    assert rows == [("Carry", 30.0, 20.0, False)]
