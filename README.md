# ChargeSquare — Stage 1 + Stage 2 (auth / admin UI)

EV charging backend: **Station Service** (connectors, tariffs, occupy/release) and **Session Service** (start/stop, cost, wallet settle, login, top-up). Optional **admin-ui** (React + Vite) for login, read-only stations/sessions, and ADMIN wallet top-up.

## One-command run (API)

```bash
docker compose up --build
```

Optional: `cp .env.example .env` then adjust. Wait until Station (`:8001`), Session (`:8002`), and Admin UI (`:8080`) are up.

Cold start with a stale DB volume:

```bash
docker compose down -v
docker compose up --build
```

Admin UI: open [http://localhost:8080](http://localhost:8080) (nginx serves the SPA and proxies `/session-api` → Session, `/station-api` → Station). Demo logins: `admin`/`admin`, `viewer`/`viewer`.

## Sample requests (auth → start → stop → top-up)

Seed: user `7` (wallet `500.00` TRY), connector `10`, demo logins `admin`/`admin` (ADMIN) and `viewer`/`viewer` (VIEWER). See [SECURITY.md](SECURITY.md).

```bash
# Health (public)
curl -s http://localhost:8001/health
curl -s http://localhost:8002/health

# Login
TOKEN=$(curl -s -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin\"}" | python -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")

# Start session
curl -s -X POST http://localhost:8002/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"userId\":7,\"connectorId\":10}"

# Stop session (replace {id} with sessionId from start)
curl -s -X POST http://localhost:8002/sessions/{id}/stop \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"energyKwh\":12.5}"

# Wallet top-up (ADMIN)
curl -s -X POST http://localhost:8002/users/7/wallet/top-up \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"amount\":50}"
```

Expected stop receipt (before top-up): `cost` **108.25**, `walletBalanceAfter` **391.75**, status `COMPLETED`.

## Admin UI (local Vite, optional)

```bash
cd admin-ui && npm install && npm run dev
```

Opens Vite on `http://localhost:5173` (proxies Session `:8002` and Station `:8001`). Prefer compose `:8080` for the full stack.

## Main endpoints

**Station** (`http://localhost:8001`) — reads need a token; occupy/release need ADMIN

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | Public |
| GET | `/connectors/{id}` | Token |
| GET | `/stations/{id}/connectors` | Token |
| POST | `/connectors/{id}/occupy` | ADMIN |
| POST | `/connectors/{id}/release` | ADMIN |

**Session** (`http://localhost:8002`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | Public |
| POST | `/auth/login` | Public |
| POST | `/sessions` | Token (VIEWER or ADMIN) |
| POST | `/sessions/{id}/stop` | Token (VIEWER or ADMIN) |
| GET | `/sessions/{id}` | Token |
| GET | `/users/{userId}/sessions` | Token |
| GET | `/users/{userId}/wallet` | Token |
| POST | `/users/{userId}/wallet/top-up` | ADMIN |

Errors use `{ "error": "CODE", "message": "..." }`.

## Stack + why

- **Python + FastAPI** — familiar, fast to ship a correct slice
- **Shared PostgreSQL** — one DB for Stage 1 simplicity (tests use in-memory SQLite only)
- **Monorepo** (`station-service/`, `session-service/`, `admin-ui/`) — easy local/CI layout
- **Wallet in Session** — in-process settle; Session → Station remains the required network hop
- **Money** — Pydantic `SafeDecimal` = `Decimal` (serialized as a JSON number). We avoid naive `float` so tariff math stays exact; final cost uses `ROUND_HALF_UP` to 2 decimals
- **Stage 2 JWT** — Bearer tokens with role claims; login on Session; both APIs verify with shared `JWT_SECRET`

## How to run tests

```bash
cd station-service && pip install -r requirements.txt && pytest -q
cd ../session-service && pip install -r requirements.txt && pytest -q
cd ../admin-ui && npm install && npm run build
```

CI (GitHub Actions) on every push: install deps → pytest both services → `docker build` both images → admin-ui build. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Kubernetes

Plain manifests under [`k8s/`](k8s/): Deployment + Service for Station and Session, plus a ConfigMap (incl. JWT/CORS placeholders) via `envFrom`.

Validated with:

```bash
kubectl apply --dry-run=client -f k8s/
```

A full cluster apply was **not** run for this submission (Postgres and container images are assumed provided separately when applying for real).

## Assumptions

- **Meter simulation**: `energyKwh` on stop is client-supplied (no live meter integration in Stage 1).
- **Insufficient balance**: stop is **rejected** with `409 INSUFFICIENT_BALANCE`; session stays `ACTIVE`; wallet is not debited (no negative balance). Use ADMIN top-up to restore funds. See [DESIGN.md](DESIGN.md).
- **Tariff mid-session**: tariff is **snapshotted at start**; stop bills from the snapshot only.
- If Station is unreachable, Session fail-fasts with `503` `STATION_UNAVAILABLE` (no retries).
- Local-demo DB / JWT credentials in `.env.example` / ConfigMap are placeholders, not production secrets.
- Cost formula: `round(energyKwh * pricePerKwh + startFee, 2)`. Duration does not affect cost.
- Cross-service consistency is best-effort — documented in [DESIGN.md](DESIGN.md).
- Session → Station calls use a short-lived service ADMIN JWT (same shared secret).

## Known limitations (honest)

- Partial-failure / idempotent-retry recovery is prose-only in DESIGN — not implemented.
- Admin UI token lives in `sessionStorage` (XSS risk noted in SECURITY.md); no refresh tokens.

## Optional parts / Stage 2

**Attempted:** JWT auth/RBAC on both APIs, wallet top-up, React admin UI (login / stations / sessions / top-up), [SECURITY.md](SECURITY.md).

**Not attempted:** third Wallet Service, brokers, `RESERVED`, time-based tariffs, ingress/HPA/mesh, recovery jobs, OAuth/refresh tokens.

## Time spent / what I'd do next

About **1 working day** Stage 1 + focused Stage 2 auth/UI pass.

**Next:**

1. `try`/`except` + `rollback()` around commits
2. SQLAlchemy 2.0 `select` / `joinedload` (style only)
3. More consistent seeding / documented recovery ideas in DESIGN

## Project layout

```text
station-service/     # connectors, tariffs, occupy/release (+ JWT)
session-service/     # sessions, cost, wallet, login, top-up
admin-ui/            # React + Vite Stage 2 panel
docker-compose.yml   # db + station + session + admin-ui
k8s/                 # plain YAML manifests
.github/workflows/   # CI
SECURITY.md          # Stage 2 auth notes
DESIGN.md            # decisions + consistency / recovery notes
DECISIONS.md         # locked planning choices
```
