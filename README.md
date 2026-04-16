# Fair Exchange Dice

Multiplayer dice game where two players challenge each other to a dice duel. Uses a **cryptographic bit-commitment scheme** so neither player can cheat.

---

## Quick Start

```bash
docker compose up -d --build
docker compose exec server python manage.py migrate
docker compose exec server python manage.py createsuperuser  # optional
```

| Service  | URL                              |
|----------|----------------------------------|
| Frontend | https://localhost:5173           |
| API      | https://localhost:8000           |
| Admin    | https://localhost:8000/admin     |
| Swagger  | https://localhost:8000/api/docs/ |

For HTTPS setup see [LOCAL_HTTPS.md](LOCAL_HTTPS.md).

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Browser (React + Vite)            │
│                                             │
│   Login/Register    Lobby    Game View      │
└────────────────────┬────────────────────────┘
                     │  HTTPS (proxied by Vite)
                     ▼
┌─────────────────────────────────────────────┐
│           Django REST API (:8000)           │
│                                             │
│   /api/auth/*  — authentication             │
│   /api/game/*  — game logic                 │
│                                             │
│   PostgreSQL                                │
│   Users, Games, OnlineStatus, JWT blacklist │
└─────────────────────────────────────────────┘
```

Vite proxies `/api/*` to Django so the frontend never calls the backend directly.

---

## How the Game Works

### Lobby

After login, the dashboard polls every 5 seconds and shows:

- **Online Players** — users with a heartbeat in the last 30 seconds
- **Incoming / Sent Challenges** — accept, decline, or wait
- **Active Games** — games in progress
- **Recent Games** — finished results

Heartbeat is sent every 15 seconds.

### Game Flow

1. **Challenge** — click Challenge next to an online player. Creates a `pending` game.
2. **Accept** — opponent accepts, game moves to `committing`.
3. **Commit** — both players roll. The browser generates a random nonce (32 bytes) and a dice value (1–6), computes `SHA-256(nonce || value)`, and sends only the hash to the server. The nonce and value stay in the browser.
4. **Reveal** — once both commitments are stored, the server transitions to `revealing`. Each player sends their nonce and value. The server recomputes the hash and rejects any mismatch.
5. **Result** — higher value wins. Ties are draws.

---

## Bit Commitment Protocol

```
commitment = SHA-256(nonce || value)
```

- **nonce** — 256-bit random, generated in the browser, unique per roll
- **value** — dice result (1–6)
- **SHA-256** — one-way hash function

### Protocol

```
Player A                    Server                    Player B
────────                    ──────                    ────────
roll → value_A
nonce_A
commit_A = H(nonce_A‖value_A)
                 ──commit_A──▶
                                                      roll → value_B
                                                      nonce_B
                                                      commit_B = H(nonce_B‖value_B)
                              ◀──commit_B──
                 (both stored → revealing)

send (nonce_A, value_A)
                 ──reveal──▶
                 verify: H(nonce_A‖value_A) == commit_A ✓
                                                      send (nonce_B, value_B)
                              ◀──reveal──
                              verify: H(nonce_B‖value_B) == commit_B ✓

                 compare values → winner
```

### Why this is fair

| Property    | Guarantee |
|-------------|-----------|
| **Hiding**  | SHA-256 is one-way — the hash reveals nothing about the value. |
| **Binding** | Once committed, a player can't change their value. Finding a collision is computationally infeasible. |

Without the nonce, an attacker could precompute `SHA-256("1")` through `SHA-256("6")` and reverse any commitment. The 256-bit random nonce makes that impossible.

The server can't cheat either — it never sees the nonce until the reveal phase.

---

## API Reference

Auth is handled via httpOnly cookies set by the server. No `Authorization` header needed.

### Authentication

| Method   | Endpoint                    | Description           |
|----------|-----------------------------|-----------------------|
| `POST`   | `/api/auth/register/`       | Create account        |
| `POST`   | `/api/auth/login/`          | Login, sets JWT cookies |
| `POST`   | `/api/auth/logout/`         | Blacklist tokens      |
| `GET`    | `/api/auth/me/`             | Current user info     |
| `DELETE` | `/api/auth/delete_account/` | Delete account        |
| `POST`   | `/api/auth/token/refresh/`  | Refresh access token  |

### Game

| Method | Endpoint                    | Description |
|--------|-----------------------------|-------------|
| `POST` | `/api/game/heartbeat/`      | Mark yourself online |
| `GET`  | `/api/game/online-users/`   | Online players (last 30s) |
| `GET`  | `/api/game/`                | Your games |
| `POST` | `/api/game/`                | Challenge a player `{ "opponent_id": 42 }` |
| `GET`  | `/api/game/{id}/`           | Game detail |
| `POST` | `/api/game/{id}/accept/`    | Accept challenge |
| `POST` | `/api/game/{id}/decline/`   | Decline challenge |
| `POST` | `/api/game/{id}/commit/`    | Submit commitment `{ "commitment": "<sha256hex>" }` |
| `POST` | `/api/game/{id}/reveal/`    | Submit reveal `{ "nonce": "...", "value": 4 }` |

### Game States

```
pending ──accept──▶ committing ──both committed──▶ revealing ──both revealed──▶ finished
       └──decline──▶ declined
```

---

## Authentication

JWT via `djangorestframework-simplejwt`:

- **Access token** — 1 hour, stored in httpOnly cookie
- **Refresh token** — 7 days, rotated on use, httpOnly cookie
- **Blacklisting** — logout invalidates both tokens immediately
- **Lockout** — 5 failed logins → 15-minute lockout

A non-httpOnly `logged_in` flag cookie lets the frontend detect auth state without exposing the tokens.

---

## Local Development

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r server/requirements.txt
cd server
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd server/frontend
npm install
npm run dev
```

Runs on `https://localhost:5173`, proxies `/api/*` to `https://localhost:8000`.

### Environment Variables

| Variable             | Default        | Description |
|----------------------|----------------|-------------|
| `DJANGO_SECRET_KEY`  | (dev key)      | Change in production |
| `DEBUG`              | `True`         | `False` in production |
| `POSTGRES_DB`        | `fairexchange`  | Database name |
| `POSTGRES_USER`      | `postgres`     | Database user |
| `POSTGRES_PASSWORD`  | `postgres`     | Database password |
| `POSTGRES_HOST`      | `db`           | Database host |

---

## Testing

```bash
cd server
python manage.py test

# With coverage
coverage run manage.py test
coverage html
```
