CREATE OR REPLACE TABLE marts.press_windows AS
WITH live AS (
    SELECT *
    FROM staging.turnovers
    WHERE NOT excluded AND loss_s IS NOT NULL
),
period_ends AS (
    SELECT match_id, period, max(timestamp_s) AS period_end_s
    FROM staging.events
    GROUP BY match_id, period
),
scoped AS (
    SELECT
        t.*,
        p.period_end_s,
        least(t.loss_s + 8, p.period_end_s) AS window_end_s,
        least(t.loss_s + 5, p.period_end_s) AS window_end_5_s,
        p.period_end_s < t.loss_s + 8 AS censored_by_period
    FROM live AS t
    INNER JOIN period_ends AS p
        ON p.match_id = t.match_id
        AND p.period = t.period
),
regain_8 AS (
    SELECT
        s.turnover_id,
        e.timestamp_s AS regain_s,
        e.x AS regain_x,
        e.y AS regain_y,
        row_number() OVER (PARTITION BY s.turnover_id ORDER BY e.index) AS rn
    FROM scoped AS s
    INNER JOIN staging.events AS e
        ON e.match_id = s.match_id
        AND e.period = s.period
        AND e.index > s.spell_end_index
        AND e.possession_team_id = s.losing_team_id
        AND e.timestamp_s >= s.loss_s
        AND e.timestamp_s <= s.window_end_s
),
regain_5 AS (
    SELECT
        s.turnover_id,
        e.timestamp_s AS regain_s,
        e.x AS regain_x,
        e.y AS regain_y,
        row_number() OVER (PARTITION BY s.turnover_id ORDER BY e.index) AS rn
    FROM scoped AS s
    INNER JOIN staging.events AS e
        ON e.match_id = s.match_id
        AND e.period = s.period
        AND e.index > s.spell_end_index
        AND e.possession_team_id = s.losing_team_id
        AND e.timestamp_s >= s.loss_s
        AND e.timestamp_s <= s.window_end_5_s
),
pressure_8 AS (
    SELECT
        s.turnover_id,
        e.timestamp_s AS first_pressure_s,
        row_number() OVER (PARTITION BY s.turnover_id ORDER BY e.index) AS rn,
        count(*) OVER (PARTITION BY s.turnover_id) AS pressures_in_window
    FROM scoped AS s
    INNER JOIN staging.events AS e
        ON e.match_id = s.match_id
        AND e.period = s.period
        AND e.type = 'Pressure'
        AND e.team_id = s.losing_team_id
        AND e.index > s.loss_index
        AND e.timestamp_s >= s.loss_s
        AND e.timestamp_s <= s.window_end_s
),
pressure_5 AS (
    SELECT
        s.turnover_id,
        e.timestamp_s AS first_pressure_s,
        row_number() OVER (PARTITION BY s.turnover_id ORDER BY e.index) AS rn
    FROM scoped AS s
    INNER JOIN staging.events AS e
        ON e.match_id = s.match_id
        AND e.period = s.period
        AND e.type = 'Pressure'
        AND e.team_id = s.losing_team_id
        AND e.index > s.loss_index
        AND e.timestamp_s >= s.loss_s
        AND e.timestamp_s <= s.window_end_5_s
),
counter AS (
    SELECT s.turnover_id
    FROM scoped AS s
    INNER JOIN staging.events AS e
        ON e.match_id = s.match_id
        AND e.period = s.period
        AND e.counterpress IS TRUE
        AND e.team_id = s.losing_team_id
        AND e.index > s.loss_index
        AND e.timestamp_s >= s.loss_s
        AND e.timestamp_s <= s.window_end_s
    GROUP BY s.turnover_id
)
SELECT
    s.turnover_id,
    s.match_id,
    s.period,
    s.losing_team,
    s.losing_team_id,
    s.winning_team,
    s.winning_team_id,
    s.loss_s,
    s.loss_minute,
    s.loss_second,
    s.loss_index,
    s.loss_type,
    s.loss_x,
    s.loss_y,
    CASE
        WHEN s.loss_x < 40 THEN 'own_third'
        WHEN s.loss_x < 80 THEN 'middle'
        ELSE 'opp_third'
    END AS loss_zone,
    s.window_end_s,
    s.censored_by_period,
    r8.regain_s IS NOT NULL AS regained,
    r8.regain_s,
    r8.regain_x,
    r8.regain_y,
    CASE
        WHEN r8.regain_s IS NULL THEN NULL
        ELSE r8.regain_s - s.loss_s
    END AS time_to_regain_s,
    CASE
        WHEN r8.regain_x IS NULL THEN NULL
        WHEN r8.regain_x < 40 THEN 'own_third'
        WHEN r8.regain_x < 80 THEN 'middle'
        ELSE 'opp_third'
    END AS regain_zone,
    r8.regain_x >= 60 AS regained_in_opp_half,
    r5.regain_s IS NOT NULL AS regained_5,
    r5.regain_x AS regain_x_5,
    r5.regain_y AS regain_y_5,
    CASE
        WHEN r5.regain_s IS NULL THEN NULL
        ELSE r5.regain_s - s.loss_s
    END AS time_to_regain_5_s,
    p8.first_pressure_s IS NOT NULL AS pressed,
    p8.first_pressure_s,
    CASE
        WHEN p8.first_pressure_s IS NULL THEN NULL
        ELSE p8.first_pressure_s - s.loss_s
    END AS time_to_first_pressure_s,
    coalesce(p8.pressures_in_window, 0) AS pressures_in_window,
    p5.first_pressure_s IS NOT NULL AS pressed_5,
    CASE
        WHEN p5.first_pressure_s IS NULL THEN NULL
        ELSE p5.first_pressure_s - s.loss_s
    END AS time_to_first_pressure_5_s,
    c.turnover_id IS NOT NULL AS statsbomb_counterpress
FROM scoped AS s
LEFT JOIN regain_8 AS r8
    ON r8.turnover_id = s.turnover_id AND r8.rn = 1
LEFT JOIN regain_5 AS r5
    ON r5.turnover_id = s.turnover_id AND r5.rn = 1
LEFT JOIN pressure_8 AS p8
    ON p8.turnover_id = s.turnover_id AND p8.rn = 1
LEFT JOIN pressure_5 AS p5
    ON p5.turnover_id = s.turnover_id AND p5.rn = 1
LEFT JOIN counter AS c
    ON c.turnover_id = s.turnover_id;
