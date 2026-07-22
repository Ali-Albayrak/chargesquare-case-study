# ChargeSquare — Stage 1

EV charging backend: **Station Service** (connectors, tariffs, occupy/release) and **Session Service** (start/stop, cost, wallet settle). Session calls Station over the network on start.

## One-command run

```bash
docker compose up --build
```

Optional: `cp .env.example .env` then adjust. Wait until Station (`:8001`) and Session (`:8002`) are healthy.

Cold start with a stale DB volume:

```bash
docker compose down -v
docker compose up --build
```

## Sample requests (start → stop)

Seed demo: user `7` (wallet `500.00` TRY), connector `10` (tariff `8.50`/kWh + `2.00` start fee).

```bash
# Health
curl -s http://localhost:8001/health
curl -s http://localhost:8002/health

# Start session
curl -s -X POST http://localhost:8002/sessions \
  -H "Content-Type: application/json" \
  -d "{\"userId\":7,\"connectorId\":10}"

# Stop session (replace {id} with sessionId from start)
curl -s -X POST http://localhost:8002/sessions/{id}/stop \
  -H "Content-Type: application/json" \
  -d "{\"energyKwh\":12.5}"
```

Expected stop receipt: `cost` **108.25**, `walletBalanceAfter` **391.75**, status `COMPLETED`. Connector `10` returns to `AVAILABLE`:

```bash
curl -s http://localhost:8001/connectors/10
```

## Main endpoints

**Station** (`http://localhost:8001`)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | Liveness |
| GET | `/connectors/{id}` | Status + tariff |
| GET | `/stations/{id}/connectors` | List connectors |
| POST | `/connectors/{id}/occupy` | Internal; `200` / `409` |
| POST | `/connectors/{id}/release` | Back to `AVAILABLE` |

**Session** (`http://localhost:8002`)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | Liveness |
| POST | `/sessions` | Start `{ userId, connectorId }` → `201` ACTIVE |
| POST | `/sessions/{id}/stop` | Stop `{ energyKwh }` → bill + settle |
| GET | `/sessions/{id}` | Session detail |
| GET | `/users/{userId}/sessions` | List by user |

Errors use `{ "error": "CODE", "message": "..." }`.

## Stack + why

- **Python + FastAPI** — familiar, fast to ship a correct slice
- **Shared PostgreSQL** — one DB for Stage 1 simplicity (tests use in-memory SQLite only)
- **Monorepo** (`station-service/`, `session-service/`) — easy local/CI layout
- **Wallet in Session** — in-process settle; Session → Station remains the required network hop
- **Money** — Pydantic `Money` = `Decimal` (serialized as a JSON number). We avoid naive `float` so tariff math stays exact; final cost uses `ROUND_HALF_UP` to 2 decimals

## How to run tests

```bash
cd station-service && pip install -r requirements.txt && pytest -q
cd ../session-service && pip install -r requirements.txt && pytest -q
```

CI (GitHub Actions) on every push: install deps → pytest both services → `docker build` both images (no registry push). See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Kubernetes

Plain manifests under [`k8s/`](k8s/): Deployment + Service for Station and Session, plus a ConfigMap (`STATION_SERVICE_URL`, `DATABASE_URL`, ports) via `envFrom`.

Validated with:

```bash
kubectl apply --dry-run=client -f k8s/
```

A full cluster apply was **not** run for this submission (Postgres and container images are assumed provided separately when applying for real).

## Assumptions

- **Meter simulation**: `energyKwh` on stop is client-supplied (no live meter integration in Stage 1).
- **Insufficient balance**: stop is **rejected** with `409 INSUFFICIENT_BALANCE`; session stays `ACTIVE`; wallet is not debited (no negative balance). Stuck-ACTIVE-without-funds is accepted for Stage 1; no wallet top-up API yet. See [DESIGN.md](DESIGN.md).
- **Tariff mid-session**: tariff is **snapshotted at start**; stop bills from the snapshot only, so later tariff edits do not change an in-flight session.
- If Station is unreachable, Session fail-fasts with `503` `STATION_UNAVAILABLE` (no retries).
- Local-demo DB credentials in `.env.example` / ConfigMap are placeholders, not production secrets.
- Cost formula: `round(energyKwh * pricePerKwh + startFee, 2)`. Duration does not affect cost.
- Cross-service consistency (occupy-then-create; complete-then-release) is best-effort — documented in [DESIGN.md](DESIGN.md), not solved with sagas/cleanup jobs.

## Known limitations (honest)

- Partial-failure / idempotent-retry recovery is prose-only in DESIGN — not implemented.

## Optional parts / Stage 2

**Not attempted:** Stage 2 admin UI, auth/RBAC, third Wallet Service, brokers, `RESERVED`, time-based tariffs, ingress/HPA/mesh, recovery jobs, wallet top-up.

## Time spent / what I'd do next

About **1 working day** for Stage 1 (domain → compose → docs/k8s/CI).

**Next (highest leverage from review notes):**

1. `try`/`except` + `rollback()` around commits
2. SQLAlchemy 2.0 `select` / `joinedload` (style only)
3. More consistent seeding
4. Convert price and currency fields to Money pydantic model
5. Documented recovery ideas already in DESIGN — only then consider cleanup jobs / Stage 2

## Project layout

```text
station-service/     # connectors, tariffs, occupy/release
session-service/     # sessions, cost, wallet
docker-compose.yml   # db + station + session
k8s/                 # plain YAML manifests
.github/workflows/   # CI
DESIGN.md            # decisions + consistency / recovery notes
DECISIONS.md         # locked planning choices
```
