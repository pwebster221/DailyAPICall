# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python 3.11+ FastAPI application ("Daily Astrological Pipeline") that orchestrates astrological data processing through Swiss Ephemeris API, OpenAI Assistants, Neo4j graph DB, and SMTP email delivery. See `README.md` for full architecture and API documentation.

### Services

| Service | Port | Purpose |
|---|---|---|
| FastAPI app | 8000 | Main API server (`python main.py` or `venv/bin/uvicorn main:app`) |
| Neo4j | 7687 (bolt), 7474 (browser) | Graph database — must be running before the app starts |
| Mailpit | 1025 (SMTP), 8025 (web UI) | Local SMTP mail catcher for dev — must be running before the app starts |

### Starting services for development

Docker containers must be running before the FastAPI app can start, because the lifespan handler initializes the scheduler which connects to Neo4j and sends a test email.

```bash
# Start Neo4j (use your chosen password via NEO4J_AUTH)
sudo docker start neo4j || sudo docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/<YOUR_NEO4J_PASSWORD> \
  neo4j:5-community

# Start Mailpit (with STARTTLS + auth-accept-any)
sudo docker start mailpit || sudo docker run -d --name mailpit \
  -p 8025:8025 -p 1025:1025 \
  -v /tmp/mailpit-certs:/certs:ro axllent/mailpit:latest \
  --smtp-tls-cert /certs/cert.pem --smtp-tls-key /certs/key.pem \
  --smtp-auth-accept-any

# Wait for Neo4j
sleep 5

# Override SMTP env vars for local mailpit (env vars take precedence over .env file)
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_USERNAME=<any_value>
export SMTP_PASSWORD=<any_value>
export EMAIL_FROM=<any_email>
export EMAIL_TO=<any_email>
export NEO4J_URI=bolt://127.0.0.1:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=<YOUR_NEO4J_PASSWORD>
export NEO4J_DATABASE=neo4j

# Start the app
cd /workspace && venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
```

### Important gotchas

- **Environment variables override `.env` file**: Pydantic-settings reads shell env vars before the `.env` file. Injected secrets (e.g. `SMTP_HOST`, `NEO4J_URI`) will override `.env` values. You must `export` overrides in the shell.
- **App won't start without Neo4j + SMTP**: The lifespan handler calls `start_scheduler()` → `pipeline.initialize_system()`, which sends a test email and verifies Neo4j. If either fails, the app raises `RuntimeError` and exits.
- **Mailpit TLS cert**: The email service hardcodes `start_tls=True`. Mailpit needs a TLS cert. A self-signed cert at `/tmp/mailpit-certs/` is generated during setup and added to the system trust store (`/usr/local/share/ca-certificates/mailpit.crt`). If the cert expires or is missing, regenerate it and run `sudo update-ca-certificates`.
- **Mock data validation bug**: The mock ephemeris data in `src/swiss_ephemeris.py` generates `HouseCusp(degree=360.0)` for house 12, but the model constraint is `lt=360`. This causes a validation error when running the pipeline with `use_mock_data=true`. This is a pre-existing issue.

### Development commands

- **Lint**: `venv/bin/ruff check .`
- **Format check**: `venv/bin/black --check .`
- **Type check**: `venv/bin/mypy src/ main.py --ignore-missing-imports`
- **Test**: `venv/bin/pytest` (no tests exist yet in the repo)
- **Run app**: See "Starting services" above
- **Swagger UI**: http://localhost:8000/docs
- **Mailpit UI**: http://localhost:8025
