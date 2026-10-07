CREATE OR REPLACE TABLE staging.turnovers AS
WITH ordered AS (
    SELECT
        p.*,
        lead(p.period) OVER w AS next_period,
        lead(p.team) OVER w AS next_team,
        lead(p.team_id) OVER w AS next_team_id,
        lead(p.start_index) OVER w AS next_start_index
    FROM staging.possessions AS p
    WINDOW w AS (PARTITION BY match_id ORDER BY period, start_index)
),
changes AS (
    SELECT *
    FROM ordered
    WHERE
        next_team_id IS NOT NULL
        AND next_period = period
        AND next_team_id != team_id
),
on_ball AS (
    SELECT
        match_id,
        spell_id,
        index,
        timestamp_s,
        minute,
        second,
        type,
        CASE
            WHEN type = 'Pass' AND pass_end_x IS NOT NULL THEN pass_end_x
            ELSE x
        END AS loss_x,
        CASE
            WHEN type = 'Pass' AND pass_end_y IS NOT NULL THEN pass_end_y
            ELSE y
        END AS loss_y
    FROM staging.events
    WHERE
        team_id = possession_team_id
        AND x IS NOT NULL
        AND type IN (
            'Pass',
            'Carry',
            'Shot',
            'Dribble',
            'Ball Receipt*',
            'Clearance',
            'Miscontrol',
            'Dispossessed',
            'Goal Keeper',
            'Shield',
            '50/50',
            'Block',
            'Error',
            'Offside'
        )
),
last_touch AS (
    SELECT *
    FROM on_ball
    QUALIFY row_number() OVER (
        PARTITION BY match_id, spell_id
        ORDER BY index DESC
    ) = 1
),
joined AS (
    SELECT
        c.match_id,
        c.period,
        c.possession_id,
        c.team AS losing_team,
        c.team_id AS losing_team_id,
        c.next_team AS winning_team,
        c.next_team_id AS winning_team_id,
        c.end_index AS spell_end_index,
        t.index AS loss_index,
        t.timestamp_s AS loss_s,
        t.minute AS loss_minute,
        t.second AS loss_second,
        t.type AS loss_type,
        t.loss_x,
        t.loss_y,
        n.type AS next_type,
        n.pass_type AS next_pass_type,
        n.shot_type AS next_shot_type
    FROM changes AS c
    LEFT JOIN last_touch AS t
        ON t.match_id = c.match_id
        AND t.spell_id = c.possession_id
    LEFT JOIN staging.events AS n
        ON n.match_id = c.match_id
        AND n.index = c.next_start_index
)
SELECT
    match_id || '-' || possession_id AS turnover_id,
    match_id,
    period,
    losing_team,
    losing_team_id,
    winning_team,
    winning_team_id,
    loss_index,
    spell_end_index,
    loss_s,
    loss_minute,
    loss_second,
    loss_type,
    loss_x,
    loss_y,
    CASE
        WHEN next_pass_type = 'Throw-in' THEN 'throw_in'
        WHEN next_pass_type = 'Goal Kick' THEN 'goal_kick'
        WHEN next_pass_type = 'Free Kick' THEN 'free_kick'
        WHEN next_pass_type = 'Corner' THEN 'corner'
        WHEN next_pass_type = 'Kick Off' THEN 'kick_off'
        WHEN next_type = 'Referee Ball-Drop' THEN 'drop_ball'
        WHEN next_shot_type = 'Penalty' THEN 'penalty'
        WHEN loss_index IS NULL THEN 'no_on_ball_event'
        ELSE NULL
    END AS exclude_reason,
    coalesce(
        next_pass_type IN ('Throw-in', 'Goal Kick', 'Free Kick', 'Corner', 'Kick Off')
        OR next_type = 'Referee Ball-Drop'
        OR next_shot_type = 'Penalty'
        OR loss_index IS NULL,
        false
    ) AS excluded
FROM joined;
