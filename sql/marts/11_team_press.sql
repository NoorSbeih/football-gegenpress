CREATE OR REPLACE TABLE marts.team_press AS
WITH sides AS (
    SELECT losing_team_id AS team_id, any_value(losing_team) AS team
    FROM staging.turnovers
    GROUP BY losing_team_id
),
live AS (
    SELECT
        losing_team_id AS team_id,
        count(*) AS live_turnovers,
        100.0 * count(*) FILTER (WHERE regained_5) / count(*) AS regain_pct_5,
        100.0 * count(*) FILTER (WHERE regained) / count(*) AS regain_pct_8,
        median(time_to_regain_s) FILTER (WHERE regained) AS median_time_to_regain_8,
        100.0 * count(*) FILTER (WHERE pressed) / count(*) AS pressure_pct_8,
        median(time_to_first_pressure_s) FILTER (WHERE pressed) AS median_time_to_pressure_8,
        100.0 * count(*) FILTER (WHERE loss_x >= 80) / count(*) AS high_turnover_share,
        count(*) FILTER (WHERE loss_zone = 'opp_third') AS n_high,
        count(*) FILTER (WHERE loss_zone = 'own_third') AS n_low,
        100.0 * count(*) FILTER (WHERE loss_zone = 'opp_third' AND regained)
            / nullif(count(*) FILTER (WHERE loss_zone = 'opp_third'), 0)
            AS high_loss_regain_pct,
        100.0 * count(*) FILTER (WHERE loss_zone = 'own_third' AND regained)
            / nullif(count(*) FILTER (WHERE loss_zone = 'own_third'), 0)
            AS low_loss_regain_pct,
        avg(regain_x) FILTER (WHERE regained) AS mean_regain_x,
        100.0 * count(*) FILTER (WHERE statsbomb_counterpress) / count(*) AS counterpress_share,
        count(*) FILTER (WHERE regained) AS n_regained_8
    FROM marts.press_windows
    GROUP BY losing_team_id
),
dropped AS (
    SELECT losing_team_id AS team_id, count(*) AS excluded_restarts
    FROM staging.turnovers
    WHERE excluded
    GROUP BY losing_team_id
)
SELECT
    s.team_id,
    s.team,
    m.competition_key AS competition,
    coalesce(l.live_turnovers, 0) AS live_turnovers,
    coalesce(d.excluded_restarts, 0) AS excluded_restarts,
    l.regain_pct_5,
    l.regain_pct_8,
    l.median_time_to_regain_8,
    l.pressure_pct_8,
    l.median_time_to_pressure_8,
    l.high_turnover_share,
    coalesce(l.n_high, 0) AS n_high,
    coalesce(l.n_low, 0) AS n_low,
    l.high_loss_regain_pct,
    l.low_loss_regain_pct,
    l.mean_regain_x,
    l.counterpress_share,
    coalesce(l.n_regained_8, 0) AS n_regained_8
FROM sides AS s
CROSS JOIN staging.meta AS m
LEFT JOIN live AS l ON l.team_id = s.team_id
LEFT JOIN dropped AS d ON d.team_id = s.team_id;
