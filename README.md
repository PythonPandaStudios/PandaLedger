# PandaLedger

A local-first personal budgeting and payroll-forecasting desktop app. See
[`docs/PRD.md`](docs/PRD.md) for the product spec and
[`CLAUDE.md`](CLAUDE.md) for contributor/AI-agent working conventions.

## Development setup

```bash
poetry install
poetry run briefcase dev
```

## Checks

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy .
poetry run pytest
```
