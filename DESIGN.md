# DESIGN — ChargeSquare Stage 1

Short design notes for the Stage 1 slice. This page summarizes DECISIONS, explains a few implementation choices, and records document-only recovery / consistency trade-offs.

## Key decisions

| Topic | Choice | Why |
|-------|--------|-----|
| Language / framework | Python + FastAPI | Most experience with FastAPI; take-home needs a simple working slice |
| Scope | Stage 1 only | Keep architecture extendable for Stage 2 later |
| Repo layout | Monorepo | Simplest for a take-home review and easy to manage |
| Database | Shared PostgreSQL | Enough for the essential slice without multi-DB ops |
| Wallet | Folded into Session (`wallet/service.py`) | Clear boundary for a future Wallet Service extract |
| Settlement | Sync in-process module | Keeps Session → Station as the required network hop |
| Dependency down | Fail-fast `502`/`503` | Clear JSON error; no hidden retries |
| Currency / seed | TRY + consistent IDs | Seed, README, and tests share one worked example |
| Insufficient balance | Reject `409 INSUFFICIENT_BALANCE` | Prepaid wallet; session stays ACTIVE; no debit |
| Tariff | Snapshot columns at start | Mid-session price changes must not alter in-flight billing |
| Stage 2 | Deferred | Skipping carries no penalty |

## Implementation notes (why things look this way)

**Money types.** API schemas use a Pydantic `Money` alias (`Decimal` + JSON serializer to a number), not `float`. Floats cannot represent money safely; `Decimal` keeps tariff math exact before rounding to 2 dp.

**SQLite in tests.** Runtime uses PostgreSQL. Test `DATABASE_URL` is in-memory SQLite so pytest needs no Docker DB. The engine branch that enables `check_same_thread=False` / `StaticPool` exists only for that SQLite path.

**`create_all` in lifespan.** Stage 1 creates tables on startup (`Base.metadata.create_all`) instead of a migration tool. Fine for a take-home; production would use Alembic (or similar) and not auto-DDL on every boot.

**Config.** Each service reads `DATABASE_URL` / `PORT` / `STATION_SERVICE_URL` from env via `app/config.py` (pydantic-settings). Compose and k8s inject the same keys.

**Mapper helpers (`to_connector_out`, `_to_session_out`).** Thin ORM → response shaping (aliases, nested tariff snapshot). Not strictly required, but keeps routers free of field mapping clutter.

**ORM defaults.** Connector status defaults to `AVAILABLE` on the ORM model. A DB `server_default` would matter with multiple writers; for this app-only writer, the ORM default is enough.

## Insufficient balance & “negative balance” risk

On stop we compute cost from the **start snapshot**, then debit. If `wallet.balance < cost`, debit raises `409 INSUFFICIENT_BALANCE` and the session stays `ACTIVE` — we do **not** allow a negative wallet. That avoids silent debt but means a user can be stuck on an ACTIVE session until they have funds (no top-up API in Stage 1). Allowing negatives would finish the stop path but hide prepaid underfunding; we rejected that and documented the trade-off here instead of coding a recovery/top-up flow.

## Distributed consistency trade-offs (document only)

These windows are unavoidable without distributed transactions or compensating actions — intentionally out of Stage 1 scope:

1. **Start:** `occupy()` can succeed on Station before Session commits the `ACTIVE` row. If create fails afterward, the connector can stay `OCCUPIED` with no session.
2. **Stop:** wallet debit + session `COMPLETED` commit can succeed before Station `release()`. If release fails, you get a completed/paid session and a stuck occupied connector.
3. **Opposite stop failure:** if release somehow succeeded but local stop did not commit (less common with our order: we release *after* commit), you could free the connector while the session still looks ACTIVE — another reason to treat cross-service steps as best-effort without a saga.

Mitigations we would consider later (not built): compensating `release` on start failure; idempotency keys on stop; cleanup job for connectors with no ACTIVE session; outbox/saga. See also the paragraphs below.

## Idempotent Stop retries (prose only — not built)

If a client times out on `POST /sessions/{id}/stop` and retries, a naive second stop could double-charge. The basic state guard helps after a *successful* first stop (`409 SESSION_NOT_ACTIVE`). The remaining risk is a settled wallet + lost HTTP response (or partial complete/release). Making retries safe means an idempotency key or durable settlement receipt and a single transactional settle+status transition — not built for Stage 1.

## Stuck connectors / partial failure (prose only — not built)

Same start/stop windows as above. Recovery ideas: timeouts + compensating release; periodic cleanup; saga/outbox — each adds complexity. Stage 1 keeps happy-path ordering and fail-fast errors.

## Known gaps / unfinished notes

- **SQLAlchemy style:** some paths still use `db.query(...)`; migrating to 2.0 `select(...)` + `joinedload` for connector/tariff reads would be cleaner.
- **Commit robustness:** not every write path wraps `commit()` in try/except with `rollback()`; that is the main robustness improvement before production.
- **Structure:** routers are thin-ish, but further split of CRUD vs domain logic, and a single shared seed story across services, would clarify ownership.
- Kubernetes validated with `kubectl apply --dry-run=client -f k8s/` (no full cluster apply); no Postgres Deployment in `k8s/`.
- No ingress, HPA, mesh, caching, rate limiting, brokers, sagas, cleanup jobs, or Stage 2 UI/auth.
