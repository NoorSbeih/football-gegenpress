# Football Gegenpress — build plan (prompt this file)

This is **not** the game-state / “do they change when leading” project. That plan is obsolete for this repo.

Paste this file into a **new empty repo** and tell the agent:

> Follow this plan. Don't rebuild Track A (pitch maps / xG / pass maps). Don't build the game-state scoreline project. Start at Phase 0, stop after each phase, show how to run it, wait for approval.

Repo name: **`football-gegenpress`**

Pitch (one paragraph): The eight seconds after a team loses the ball. StatsBomb open event data: detect the turnover, start a clock, map where the ball is won back (or not), and how fast the first pressure arrives. That is gegenpressing as a measurement — something a pass map cannot show.

---

## Context (do not ignore)

Builder: **Noor Sbeih** — backend/full-stack (Django, React/Next.js, Postgres), public portfolio for remote-first / Spain–EU roles.

Already shipped:

- **Track A:** https://github.com/NoorSbeih/football-data-explorations  
  StatsBomb → Python package → FastAPI → Next.js pitchboard (xG / shots / **passes**).  
  **This project must not be another pass map.** Pass maps show circulation in possession. This shows what happens **immediately after possession dies**.
- **Track B:** https://github.com/NoorSbeih/city-weather-pipeline  
  Habits to reuse: layers, idempotent rebuilds, SQL where it fits, mocked tests, CI, honest README.

Football project #2: **turnover → clock → regain / pressure**. Scouting-shaped, measurable, interviewable.

Honest baseline: descriptive, not causal. Open-data samples are small. State the definition of a “loss” in the README so a coach can argue with it.

---

## The analytical question

When a team loses the ball, how often do they win it back within **eight seconds**, **where**, and **how quickly does pressure arrive**?

That is the Klopp / gegenpress idea as a statistic:

- Not “they pass a lot in the final third” (Track A already shows passing).
- Not “they have high PPDA over a whole match” (that mixes settled defence and the first five seconds).
- Specifically: **the first 8 seconds of the opponent’s new possession**.

Interview soundbite: “The pitchboard showed completed passes. This one starts the clock at the moment the pass fails — regain location, time-to-pressure, time-to-regain.”

---

## Locked stack (do not re-decide)

| Layer | Choice |
|---|---|
| Language | Python 3.11+, `src/` layout, `pyproject.toml`, ruff, pytest |
| Source | StatsBomb open data via `statsbombpy` (free, no auth) |
| Raw cache | Parquet under `data/raw/` (**gitignored**) |
| Warehouse | **DuckDB** file locally. SQL in `sql/` (CTEs, `LEAD`/`LAG`, interval joins) |
| Layers | `raw` → `staging` → `marts` |
| Orchestration | **Prefect 2.x** flow: extract → load → transform → export |
| Serving | **No always-on API.** JSON into `web/public/data/`. Static Next.js (App Router, TS) on **Vercel free** |
| Charts | One library (Recharts or Observable Plot) + a simple pitch SVG (reuse coordinate math, **not** Track A components) |
| Container | Optional `docker-compose` one-shot `build` |
| CI | GitHub Actions: ruff + pytest + `next lint` + `next build` |

**Do not add:** Kafka, Spark, paid cloud DB, custom xG model, player heatmaps as the homepage, live scraping.

---

## Data scope

v1: **FIFA World Cup 2022** (confirm IDs with `sb.competitions()`, store in `config/competitions.yaml`).

Later (only after v1 is live): Euro 2024, WC 2018.

---

## Definitions (lock with tests; look up real StatsBomb field names in a fixture dump — do not guess)

### What counts as “losing the ball”

A **turnover** is the first event of a **new opposition possession** that is not a restart the losing team cannot press (see exclusions).

Practical construction:

1. Order events by `(match_id, period, index)`.
2. Possession identity: StatsBomb `possession` / `possession_team` (verify on a real dump).
3. A turnover for team A occurs when possession_team **changes from A to B** (or equivalent possession-id change with a new team).
4. The **loss location** is the location of the last on-ball event by team A in the old possession (incomplete pass end location if present, else event `location`).
5. The **loss time** is that event’s timestamp (seconds from period start + period offset), **not** `minute`.

Exclusions (do **not** start an 8-second clock):

- **Set-piece restarts** the opponent is allowed to take slowly: goal kick, throw-in, corner, free kick, kick-off, penalty, drop ball — unless you can prove from the events that play restarted and the first opponent action is live. v1: **exclude turnovers whose next possession starts with a set-piece restart type.**
- **Period 5 (penalty shootout)** — ignore entirely.
- **Out of play leading to a stoppage** longer than the window (the clock is about *live* counterpress). If the next event is a dead-ball restart, drop the window.

Document the exclusion count in the README (“N turnovers dropped as restarts”).

### The eight-second window

From `loss_time`, look forward in the **same period** (do not cross half-time / extra-time breaks):

- Window end = `loss_time + 8 seconds`, or period end, whichever is first.
- If the period ends first, mark the window `censored_by_period`.

**Sensitivity:** also compute 5s (common in the literature). Store both; UI default is **8s**.

### Regain (winning it back)

A **regain** is the first event in the window where `possession_team` is again the team that lost the ball (or a clear on-ball recovery: ball recovery / interception / tackle won — **whichever the fixture dump supports; pick one primary rule and test it**).

- `time_to_regain_s` = regain timestamp − loss timestamp.
- If no regain in 8s: `regained = false`, `time_to_regain_s` is null (do not impute 8).
- **Regain location** = that event’s `location`.

Classify regain zone from StatsBomb pitch (120×80):

- `own_third` (x < 40)
- `middle` (40–80)
- `opp_third` (x ≥ 80)

Also: `regained_in_opp_half` (x ≥ 60).

### Pressure arrival

A **pressure event** is StatsBomb type `Pressure` (and optionally `Foul Committed` that is a counterpress foul — v1: Pressure only, plus `counterpress == true` if the flag exists on the event).

- `time_to_first_pressure_s` = first Pressure by the losing team in the window − loss time.
- If none: null, `pressed = false`.
- `pressures_in_window` = count.

StatsBomb often has a **`counterpress`** boolean on the event that *starts* the opponent possession or on the first defensive actions. **Use it as a cross-check, not as the only definition.** Report: “our 8s regain rate vs share of turnovers StatsBomb tagged counterpress.” If they disagree a lot, investigate before shipping the UI.

### Headline metrics (per team, per competition)

Rates are **per 100 live turnovers** (after exclusions), not per 90 minutes — the unit is the turnover.

| Metric | Definition |
|---|---|
| Live turnovers | Count after exclusions |
| Regain % ≤5s | 100 × regains within 5s / live turnovers |
| Regain % ≤8s | 100 × regains within 8s / live turnovers |
| Median time to regain | Among windows that regained ≤8s |
| Pressure % ≤8s | Share of windows with ≥1 pressure |
| Median time to first pressure | Among windows that pressed |
| High turnover share | Share of losses with x ≥ 80 (they lost it high) |
| High-loss regain % | Regain ≤8s **given** the loss was in the opp third (true gegenpress) |
| Low-loss regain % | Same given loss in own third (just “defending,” not gegenpress) |
| Mean regain height | Mean x of successful regains |

**The insight that is not a pass map:** split **high losses** vs **low losses**. A team can have a high overall regain % because they defend their box well. Gegenpressing is **regain after losing it in the opponent’s half / third**.

Sample size: hide a team if **&lt; 40 live turnovers**. Show N next to every number.

### Pitch pictures (two, not twenty)

1. **Loss locations** (where they give it away), hex or binned counts, one team.
2. **Successful 8s regains** (where they win it back), same pitch.  
   Optional third: arrows loss → regain for a single match (small multiples later).

Do not ship a pass-network view.

---

## Warehouse model (DuckDB)

```
raw.matches
raw.events

staging.events              typed: match_id, period, index, timestamp_s,
                            team, possession, possession_team, type,
                            x, y, end_x, end_y, counterpress, outcome, ...

staging.possessions         possession_id, team, start_index, end_index, start_s, end_s
staging.turnovers           one row per live loss: match_id, losing_team, winning_team,
                            loss_s, loss_x, loss_y, loss_type, excluded, exclude_reason

marts.press_windows         turnover_id, window_end_s, regained, regain_s, regain_x, regain_y,
                            time_to_regain_s, pressed, first_pressure_s, time_to_first_pressure_s,
                            pressures_in_window, loss_zone, regain_zone, censored_by_period

marts.team_press            team, competition, all headline metrics + N
marts.match_turnovers       for the match view (list of windows)
```

`CREATE OR REPLACE TABLE` — full rebuild, dataset is small.

---

## Repo layout

```
football-gegenpress/
  pyproject.toml
  README.md
  LICENSE                          MIT, Noor Sbeih
  .gitignore                       data/raw, *.duckdb, .venv, node_modules, .next
  config/competitions.yaml
  src/gegenpress/
    config.py
    extract.py                     statsbombpy → parquet cache
    load.py
    transform.py                   runs sql/ in order
    export.py                      marts → web/public/data/*.json
    flows.py                       Prefect
    cli.py                         `gegenpress build [--competition wc2022]`
  sql/
    staging/01_events.sql
    staging/02_possessions.sql
    staging/03_turnovers.sql
    marts/10_press_windows.sql
    marts/11_team_press.sql
  tests/
    fixtures/                      tiny event lists (no network)
    test_turnovers.py
    test_windows.py
    test_metrics.py
  web/                             Next.js App Router + TS
    public/data/                   committed JSON
  .github/workflows/ci.yml
```

---

## UI (thin)

WC 2022 only in v1. Three views:

1. **League / tournament table** — teams ranked by **high-loss regain % ≤8s** (the gegenpress number), with overall 8s regain %, median time-to-pressure, N turnovers. Sortable. Insufficient N labelled.
2. **Team pitch** — loss hex vs regain hex; toggle 5s/8s; caption states the definition in one sentence.
3. **Match tape** — one match: each live turnover as a row (time, zone, regained Y/N, seconds, pressure seconds). Default match: a press-heavy side if the data supports it (e.g. a Germany / Spain / Japan game — **pick after you look at N**, don’t hardcode a narrative).

No player page in v1. No pass maps. Empty state: “not enough live turnovers.”

JSON:

- `competitions.json`
- `teams/wc2022.json`
- `pitches/{team_id}.json` (binned cells, not raw thousands of points if file size explodes — bin in the warehouse)
- `matches/{match_id}.json`

---

## Tests (no network)

Hand-built fixtures:

- Incomplete pass in open play → one turnover for the passer’s team; window starts at that event.
- Opponent then loses it back at +3s → `regained=true`, `time_to_regain_s ≈ 3`.
- Opponent keeps it for 12s → `regained=false`.
- Goal kick / corner starting the next possession → **excluded**, no window.
- Shootout (period 5) → no turnovers.
- Period ends at +4s → `censored_by_period`, no fake regain.
- Pressure at +1.2s → `time_to_first_pressure_s` set; no pressure → null.
- Own-half loss vs opp-third loss both counted, but **high-loss regain %** only uses the high-loss denominator.
- Two possessions in a row for the same team (if StatsBomb splits them) must not create a phantom turnover — write the rule after inspecting a real match dump.

If StatsBomb field names differ from this doc, dump one match’s columns in Phase 1, write a mapping table in the README, and test against **real** types from that dump.

---

## CI

Push/PR to `main`: ruff check + format --check, pytest, `npm ci && npm run lint && npm run build` in `web/`.

---

## Deploy

Vercel static `web/`. JSON committed. No paid DB. Live URL + GIF in README.

---

## Phases (stop after each)

### Phase 0 — scaffold

Structure, LICENSE, gitignore, pyproject, empty package, Next hello-world, CI, first commit.

### Phase 1 — extract + load WC 2022

Parquet cache; DuckDB raw; print match/event counts; **write `docs/event-fields.md`** from one real match: types, possession fields, whether `counterpress` exists, location columns.

**Done when:** second build skips HTTP; field mapping is written from evidence.

### Phase 2 — possessions, turnovers, 8s windows

This is the core. Unit tests above. Print: live turnovers, excluded restarts, regain% at 5s/8s for the tournament.

**Done when:** tests pass and tournament-level rates are sane (regain ≤8s should not be 90% or 2% — if so, the definition is wrong; fix before UI).

### Phase 3 — team marts + high vs low split

`marts.team_press`. Print top/bottom high-loss regain %. Read them as a fan; investigate nonsense.

### Phase 4 — export + UI

Three views. Bin pitches in SQL so JSON stays small.

### Phase 5 — ship

README: question, **exact** loss/window/regain rules, exclusions, 5s vs 8s, confounders (scoreline, opponent quality, open-play only). Architecture mermaid. Vercel + GIF.

---

## README must include

1. One-line question + live link  
2. Why this is not a pass map  
3. Definitions (loss, 8s, regain, pressure, exclusions)  
4. High-loss vs low-loss split  
5. Limitations  
6. StatsBomb → Parquet → DuckDB → JSON → Next.js  
7. How to run  

---

## Definition of done (v1)

- [ ] Public repo, MIT, method-first README  
- [ ] WC 2022 live turnovers + 8s windows in DuckDB  
- [ ] Tests for exclusions, regain, pressure, period boundary  
- [ ] Team table + pitch + match tape  
- [ ] CI green  
- [ ] Live Vercel URL  

---

## Agent rules

- First commit early.  
- Do **not** copy football-data-explorations UI.  
- Do **not** implement game-state / winning-drawing-losing.  
- Inspect real StatsBomb events before writing SQL.  
- Never commit parquet or `.duckdb`.  
- Prefer SQL for windows (`LEAD` possession_team, time differences); Python for extract/export.  

## How to run (target)

```bash
python -m venv .venv
pip install -e ".[dev]"
gegenpress build --competition wc2022
cd web && npm ci && npm run dev
```
