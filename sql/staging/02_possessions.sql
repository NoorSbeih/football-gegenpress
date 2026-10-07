CREATE OR REPLACE TABLE staging.possessions AS
SELECT
    match_id,
    spell_id AS possession_id,
    period,
    any_value(possession_team) AS team,
    any_value(possession_team_id) AS team_id,
    min(index) AS start_index,
    max(index) AS end_index,
    min(timestamp_s) AS start_s,
    max(timestamp_s) AS end_s
FROM staging.events
GROUP BY match_id, spell_id, period;
