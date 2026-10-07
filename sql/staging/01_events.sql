CREATE OR REPLACE TABLE staging.events AS
WITH base AS (
    SELECT
        match_id,
        period,
        index,
        timestamp,
        minute,
        second,
        type,
        team,
        team_id,
        possession,
        possession_team,
        possession_team_id,
        play_pattern,
        pass_type,
        pass_outcome,
        shot_type,
        counterpress,
        try_cast(json_extract(location, '$[0]') AS DOUBLE) AS x,
        try_cast(json_extract(location, '$[1]') AS DOUBLE) AS y,
        try_cast(json_extract(pass_end_location, '$[0]') AS DOUBLE) AS pass_end_x,
        try_cast(json_extract(pass_end_location, '$[1]') AS DOUBLE) AS pass_end_y,
        date_diff(
            'microsecond',
            TIME '00:00:00',
            try_cast(timestamp AS TIME)
        ) / 1000000.0 AS timestamp_s
    FROM raw.events
    WHERE period != 5
),
marked AS (
    SELECT
        *,
        CASE
            WHEN lag(period) OVER w IS NULL THEN 1
            WHEN period IS DISTINCT FROM lag(period) OVER w THEN 1
            WHEN possession_team_id IS DISTINCT FROM lag(possession_team_id) OVER w THEN 1
            ELSE 0
        END AS new_spell
    FROM base
    WINDOW w AS (PARTITION BY match_id ORDER BY period, index)
)
SELECT
    * EXCLUDE (new_spell),
    sum(new_spell) OVER (
        PARTITION BY match_id
        ORDER BY period, index
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS spell_id
FROM marked;
