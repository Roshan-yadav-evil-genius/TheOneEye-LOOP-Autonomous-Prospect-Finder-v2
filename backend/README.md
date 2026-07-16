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

### Create a Virtual Environment & Install

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the API

The API uses FastAPI. You can run the server locally using Uvicorn (make sure to set `PYTHONPATH=src`):

```bash
PYTHONPATH=src uvicorn main:app --reload --port 7878
```

## Command Line Interface (CLI)

The backend provides a CLI to manage workers, database schemas, and data seeding. Since this project is run directly from source, prefix CLI commands with `PYTHONPATH=src python -m cli` instead of `loop`.

### Database Bootstrap & Seeding

Initialize the database schema (creates SQLite schema by default):
```bash
PYTHONPATH=src python -m cli bootstrap
```

Seed the database with sample data (organizations, products, sales strategies):
```bash
PYTHONPATH=src python -m cli seed
```

### Background Workers

Run the durable worker loop for background tasks:
```bash
PYTHONPATH=src python -m cli worker
```
(Alternatively, run one cycle with `PYTHONPATH=src python -m cli worker-once`)

Run the scheduler for background jobs:
```bash
PYTHONPATH=src python -m cli scheduler
```
(Alternatively, run one cycle with `PYTHONPATH=src python -m cli scheduler-once`)

Consume Redis Streams into idempotent inbox handlers:
```bash
PYTHONPATH=src python -m cli consume-once
```

### Other Commands
Rebuild progress projection evidence for a specific sales strategy:
```bash
PYTHONPATH=src python -m cli reconcile <strategy_id>
```

Check the CLI version:
```bash
PYTHONPATH=src python -m cli version
```
