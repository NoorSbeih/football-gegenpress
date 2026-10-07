# Event fields

Written from one real open-data match, not from the plan's guessed names.

Sample: match `3857276`, Canada vs Morocco, 2022-12-01. `statsbombpy` with no credentials. 3,388 events, 91 flattened columns. Raw JSON for the same match is the StatsBomb open-data file `events/3857276.json`.

Competition row used for the extract, from `sb.competitions()` on 2026-10-07:

| competition_id | season_id | competition_name | season_name | gender |
| --- | --- | --- | --- | --- |
| 43 | 106 | FIFA World Cup | 2022 | male |

This match is one group game. Other matches can add columns (a shootout, a card type this game never used). `raw.events` is loaded with `union_by_name=true` for that reason. This file does not claim these counts for the whole tournament.

## What the cache stores

`sb.events(match_id)` with the default `flatten_attrs=True`. Nested objects are already flattened to columns. Lists and dicts are then JSON strings in parquet, because a column of Python lists is not a stable parquet type. Nullable bools stay booleans.

`location` in DuckDB is the string `[61.0, 40.1]`, not two numeric columns. Phase 2 parses it.

## Names that matter

| JSON | Column we store | This match | Notes |
| --- | --- | --- | --- |
| `type.name` | `type` | `Pass` | string. Values below. |
| `possession` | `possession` | `2` | int. Possession sequence id inside the match. |
| `possession_team.name` | `possession_team` | `Morocco` | string. Always filled (3,388/3,388). |
| `possession_team.id` | `possession_team_id` | `788` | int. Canada is `1833`, Morocco is `788` in this match. |
| `team.name` | `team` | `Canada` | who performed the event. Not always `possession_team`. |
| `team.id` | `team_id` | `1833` | int |
| `location` | `location` | `[76.6, 1.9]` | JSON `[x, y]`. 3,359 non-null, every one length 2. Pitch is 120 by 80. |
| `pass.end_location` | `pass_end_location` | `[111.9, 47.9]` | JSON `[x, y]` on passes. |
| `carry.end_location` | `carry_end_location` | `[48.4, 42.5]` | JSON `[x, y]` on carries. |
| `goalkeeper.end_location` | `goalkeeper_end_location` | `[1.6, 41.0]` | JSON `[x, y]`. 10 values, all length 2. |
| `shot.end_location` | `shot_end_location` | `[120.0, 43.3, 1.4]` | JSON list. 5 of length 2, 7 of length 3 (the third number is height). |
| `counterpress` | `counterpress` | `true` | See below. |
| `under_pressure` | `under_pressure` | `true` | Different flag. 608 events. Not a Pressure event. |
| `timestamp` | `timestamp` | `00:00:16.870` | string, clock from the start of the period, not `minute`. |
| `minute`, `second` | `minute`, `second` | `0`, `16` | ints. Coarser than `timestamp`. |
| `period` | `period` | `1` | int. This match only has periods 1 and 2. |
| `index` | `index` | `23` | int. Unique, 1 through 3388, in event order. |
| `play_pattern.name` | `play_pattern` | `From Kick Off` | string. Values below. |
| `pass.outcome.name` | `pass_outcome` | `Incomplete` | null when the pass has no outcome tag. |
| `pass.type.name` | `pass_type` | `Throw-in` | null on an ordinary open-play pass. |

Other nested columns on this match (`related_events`, `shot_freeze_frame`, `tactics`, `50_50`) are stored the same way: JSON text. They are not inputs to the press window.

## `counterpress` exists

The key is absent on most raw events. When present, the only value in this match is `true` (never `false`). 100 of 3,388 events.

| type | events with counterpress true |
| --- | --- |
| Pressure | 58 |
| Duel | 13 |
| Foul Committed | 10 |
| Block | 7 |
| Interception | 6 |
| Dribbled Past | 4 |
| Pass | 2 |

Example, raw index 73: `type` Pressure, `team` Canada, `possession_team` Morocco, `location` `[47.1, 46.8]`, `counterpress` true.

`under_pressure` is a separate column (608 true, rest null). It marks the player on the ball, not our "first Pressure event" clock.

## `team` is not `possession_team`

588 of 3,388 events have `team != possession_team`.

Example, index 23: `type` Pressure, `team` Canada, `possession` 2, `possession_team` Morocco, `timestamp` `00:00:16.870`, `location` `[76.6, 1.9]`, `counterpress` null, `play_pattern` `From Kick Off`.

A press action is often recorded against the opponent's possession id. Phase 2 has to use `possession_team` for who has the ball and `team` for who did the event.

## `type` values in this match

Pass 955, Ball Receipt* 868, Carry 782, Pressure 289, Ball Recovery 93, Duel 63, Clearance 41, Dribble 39, Miscontrol 32, Foul Committed 31, Foul Won 31, Block 27, Dispossessed 23, Dribbled Past 23, Interception 23, Goal Keeper 16, Shot 12, Substitution 10, Tactical Shift 5, Half Start 4, Half End 4, Injury Stoppage 4, Referee Ball-Drop 4, Starting XI 2, 50/50 2, Error 1, Shield 1, Own Goal For 1, Own Goal Against 1, Offside 1.

There is a `Pressure` type. There is no column named `outcome` by itself; pass outcomes live in `pass_outcome`.

## `play_pattern` values

Regular Play 1247, From Throw In 950, From Free Kick 720, From Goal Kick 175, From Kick Off 123, From Corner 92, Other 52, From Counter 18, From Keeper 11.

## `pass_type` and `pass_outcome`

`pass_type` is null on 3,226 events (most events are not a typed restart). Non-null values: Recovery 53, Throw-in 43, Free Kick 35, Goal Kick 11, Corner 8, Interception 7, Kick Off 5.

`pass_outcome`: null 3,223, Incomplete 134, Out 21, Pass Offside 7, Unknown 3.

An incomplete pass does not by itself start the next possession on the following row. Index 55 is a Morocco pass with `pass_outcome` Incomplete. Index 56 is still Morocco, type `Ball Receipt*`, same `possession` 2.
