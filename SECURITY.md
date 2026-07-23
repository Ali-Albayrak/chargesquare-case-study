# SECURITY — ChargeSquare Stage 2

Auth/RBAC notes for the optional Stage 2 slice. Demo-only credentials; no production IdP.

## Model

- **JWT Bearer** (`Authorization: Bearer <token>`). Issued by Session `POST /auth/login`.
- Claims: `sub` (username), `role` (`VIEWER` | `ADMIN`), `exp`.
- Shared `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` on Session and Station (env / ConfigMap).
- Roles are **in the token**; backends enforce them (not UI alone).
- No refresh tokens, OAuth, password reset, or rate limiting.

## Demo accounts (seeded)

| Username | Password | Role |
|----------|----------|------|
| `viewer` | `viewer` | VIEWER |
| `admin` | `admin` | ADMIN |

Passwords stored as bcrypt hashes in `auth_accounts`. Charging wallet user `7` stays separate.

## What is protected

| Surface | Rule |
|---------|------|
| `GET /health` | Public (compose/k8s probes) |
| `POST /auth/login` | Public |
| Session reads (`GET /sessions/*`, `GET /users/*/sessions`) | Valid token |
| Session start/stop (`POST /sessions`, stop) | valid token |
| Wallet top-up | ADMIN |
| Station reads (`GET /connectors/*`, `GET /stations/*/connectors`) | Valid token |
| Station occupy/release | ADMIN |
| Session → Station internal calls | Service JWT (`sub=session-service`, `role=ADMIN`) minted with the same secret |

## CORS

`CORS_ORIGINS` is an explicit allow-list (default `http://localhost:5173`). No `*` with credentials.

## Token storage (admin UI)

Access token in `sessionStorage`. XSS can steal it; acceptable for this demo. Prefer HttpOnly cookies + refresh in a real system (out of scope).

## Audit logging

Log lines (INFO) for: login success/failure, session start/stop, cost charged, wallet debit, wallet top-up (actor username + amount + balance after).

## Secrets

All secrets from env / ConfigMap. `.env.example` holds placeholders only — never commit live secrets.
