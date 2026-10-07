CREATE OR REPLACE TABLE marts.pitch_bins AS
WITH cells AS (
    SELECT
        losing_team_id AS team_id,
        'loss' AS layer,
        8 AS window_s,
        least(11, greatest(0, floor(loss_x / 10)))::INTEGER AS bx,
        least(7, greatest(0, floor(loss_y / 10)))::INTEGER AS by_
    FROM marts.press_windows
    WHERE loss_x IS NOT NULL AND loss_y IS NOT NULL
    UNION ALL
    SELECT
        losing_team_id,
        'regain',
        8,
        least(11, greatest(0, floor(regain_x / 10)))::INTEGER,
        least(7, greatest(0, floor(regain_y / 10)))::INTEGER
    FROM marts.press_windows
    WHERE regained AND regain_x IS NOT NULL AND regain_y IS NOT NULL
    UNION ALL
    SELECT
        losing_team_id,
        'regain',
        5,
        least(11, greatest(0, floor(regain_x_5 / 10)))::INTEGER,
        least(7, greatest(0, floor(regain_y_5 / 10)))::INTEGER
    FROM marts.press_windows
    WHERE regained_5 AND regain_x_5 IS NOT NULL AND regain_y_5 IS NOT NULL
)
SELECT team_id, layer, window_s, bx, by_ AS bin_y, count(*) AS n
FROM cells
GROUP BY team_id, layer, window_s, bx, by_;
