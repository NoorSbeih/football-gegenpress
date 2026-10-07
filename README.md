# Football Gegenpress

The eight seconds after a team loses the ball.

StatsBomb open event data, measured as a turnover, a clock, and a regain — not as a pass map. This repository is the Phase 0 scaffold. Extraction, the 8-second windows, and the three views come in later phases.

## Stack

Python 3.11, DuckDB, Prefect 2, parquet cache, static Next.js. World Cup 2022 is the v1 competition. Competition IDs are confirmed in Phase 1, not guessed here.

## How to run

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
gegenpress
gegenpress build --competition wc2022
```

`gegenpress build` exits with a message that the pipeline is not implemented yet. That is expected in Phase 0.

Web:

```powershell
cd web
npm ci
npm run lint
npm run dev
```

Open http://localhost:3000. `npm run lint` runs ESLint. Next.js 16 removed the `next lint` command, so the script calls ESLint directly. `npm run build` is the production check that CI runs.
