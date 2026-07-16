# LOOP API

LOOP modular-monolith API foundation.

## Tech Stack

- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Database / ORM:** SQLAlchemy (async), Alembic for migrations
- **AI / Agents:** LangChain, LangGraph
- **Message Broker / Cache:** Redis
- **Observability:** OpenTelemetry, Prometheus

## Setup and Installation

This project uses modern Python packaging via `pyproject.toml`.

### Create a Virtual Environment & Install

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

For development and testing dependencies:
```bash
pip install -e ".[test]"
```

## Running the API

The API uses FastAPI. You can run the server locally using Uvicorn:

```bash
uvicorn loop_api.main:app --reload
```

## Command Line Interface (CLI)

The backend provides a `loop` CLI to manage workers, database schemas, and data seeding.

### Database Bootstrap & Seeding

Initialize the database schema (creates SQLite schema by default):
```bash
loop bootstrap
```

Seed the database with sample data (organizations, products, sales strategies):
```bash
loop seed
```

### Background Workers

Run the durable worker loop for background tasks:
```bash
loop worker
```
(Alternatively, run one cycle with `loop worker-once`)

Run the scheduler for background jobs:
```bash
loop scheduler
```
(Alternatively, run one cycle with `loop scheduler-once`)

Consume Redis Streams into idempotent inbox handlers:
```bash
loop consume-once
```

### Other Commands
Rebuild progress projection evidence for a specific sales strategy:
```bash
loop reconcile <strategy_id>
```

Check the CLI version:
```bash
loop version
```
