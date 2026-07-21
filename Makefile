# Sentinel — dev/demo targets. On Windows without `make`, use the PowerShell
# equivalents in scripts/ (see README) — every target maps 1:1.

BACKEND = backend
FRONTEND = frontend

.PHONY: install seed test api web demo lint

install:                       ## install backend (uv) + frontend (npm) deps
	cd $(BACKEND) && uv venv --python 3.11 && uv pip install -e ".[dev]"
	cd $(FRONTEND) && npm install

seed:                          ## reset DB to the calm demo state
	cd $(BACKEND) && uv run python -m app.seed.seed

test:                          ## run backend unit tests (sim + agents)
	cd $(BACKEND) && uv run pytest -q

api:                           ## run the FastAPI backend on :8000
	cd $(BACKEND) && uv run uvicorn app.main:app --reload --port 8000

web:                           ## run the Vite frontend on :5173
	cd $(FRONTEND) && npm run dev

# Full offline demo: seed calm state, then replay the escalation through the
# pipeline (no servers needed to prove the loop). For the visual demo, run
# `make api` + `make web` in two terminals and click "Run escalation demo".
demo: seed
	cd $(BACKEND) && uv run python -m app.seed.inject_escalation

lint:                          ## ruff + black check
	cd $(BACKEND) && uv run ruff check app && uv run black --check app
