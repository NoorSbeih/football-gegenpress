def test_high_loss_regain_ignores_low_losses(connection) -> None:
    row = connection.execute(
        """
        SELECT
            live_turnovers,
            n_high,
            n_low,
            high_loss_regain_pct,
            low_loss_regain_pct,
            regain_pct_8,
            regain_pct_5
        FROM marts.team_press
        WHERE team = 'HighSide'
        """
    ).fetchone()
    live, n_high, n_low, high_pct, low_pct, pct8, pct5 = row
    assert live == 3
    assert n_high == 2
    assert n_low == 1
    assert high_pct == 50
    assert low_pct == 0
    assert abs(pct8 - (100 / 3)) < 1e-6
    # The only regain is at +2s, so the 5s rate matches the 8s rate.
    assert abs(pct5 - (100 / 3)) < 1e-6
