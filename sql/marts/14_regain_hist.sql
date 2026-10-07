CREATE OR REPLACE TABLE marts.regain_hist AS
SELECT
    losing_team_id AS team_id,
    8 AS window_s,
    least(7, greatest(0, floor(time_to_regain_s)))::INTEGER AS bucket,
    count(*) AS n
FROM marts.press_windows
WHERE regained AND time_to_regain_s IS NOT NULL
GROUP BY losing_team_id, bucket
UNION ALL
SELECT
    losing_team_id,
    5,
    least(4, greatest(0, floor(time_to_regain_5_s)))::INTEGER,
    count(*)
FROM marts.press_windows
WHERE regained_5 AND time_to_regain_5_s IS NOT NULL
GROUP BY losing_team_id, least(4, greatest(0, floor(time_to_regain_5_s)))::INTEGER;
