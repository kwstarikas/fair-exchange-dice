# Fair Exchange Dice

A multiplayer dice game where two logged-in players challenge each other to a dice duel. The winner is determined fairly using a **cryptographic bit-commitment scheme** — neither player can cheat by choosing their value after seeing the opponent's roll.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [How the Game Works](#how-the-game-works)
4. [The Bit Commitment Protocol](#the-bit-commitment-protocol)
5. [Why This Is Fair](#why-this-is-fair)
6. [API Reference](#api-reference)
7. [Authentication](#authentication)
8. [Local Development](#local-development)
9. [Testing](#testing)

---

## Quick Start

```bash
# Start all services
docker compose up -d --build

# Apply database migrations (first run)
docker compose exec server python manage.py migrate

# Create a superuser (optional, for Django admin)
docker compose exec server python manage.py createsuperuser
```

| Service  | URL                          | Description              |
|----------|------------------------------|--------------------------|
| Frontend | http://localhost:5173        | React app (Vite)         |
| Django   | http://localhost:8000        | REST API                 |
| Admin    | http://localhost:8000/admin  | Django admin panel       |
| Swagger  | http://localhost:8000/api/docs/ | Interactive API docs  |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Browser (React + Vite)          │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Login / │  │  Lobby   │  │  Game    │  │
│  │ Register │  │ (poll    │  │  View    │  │
│  └──────────┘  │  2s)     │  └──────────┘  │
│                └──────────┘                 │
└────────────────────┬────────────────────────┘
                     │  HTTP (proxied by Vite)
                     ▼
┌─────────────────────────────────────────────┐
│           Django REST API (:8000)           │
│                                             │
│  /api/auth/*    — JWT authentication        │
│  /api/game/*    — game logic                │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │            PostgreSQL               │   │
│  │  Users, Games, OnlineStatus,        │   │
│  │  JWT token blacklist                │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

The Vite dev server proxies all `/api/*` requests to Django on port 8000, so the frontend never needs to know the backend's address directly.

---

## How the Game Works

### 1. Lobby

After logging in, every player sees:

- **Online Players** — users who sent a heartbeat within the last 30 seconds
- **Incoming Challenges** — other players who challenged you (accept or decline)
- **Sent Challenges** — challenges you sent that are waiting for a response
- **Active Games** — games currently in progress (click to open)
- **Recent Games** — finished games with the result (Win / Loss / Draw)

The frontend sends a heartbeat to `POST /api/game/heartbeat/` every 15 seconds and polls `GET /api/game/` and `GET /api/game/online-users/` every 2 seconds to keep the lobby up to date.

### 2. Challenging a Player

Click **Challenge** next to any online player. This creates a `Game` record in the database with state `pending` and immediately opens the game view showing "Waiting for opponent to accept…".

### 3. Accepting / Declining

The challenged player sees the incoming challenge in their lobby. Accepting transitions the game to `committing`. Declining removes it.

### 4. Rolling (Commit Phase)

Both players are now in the **committing** phase. Each player sees a **Roll Dice** button. The order does not matter — both must roll before either result is revealed.

When a player clicks Roll Dice:

1. The browser generates a cryptographically random **nonce** (32 bytes via `crypto.getRandomValues`)
2. The browser randomly picks a **dice value** (1–6)
3. The browser computes `commitment = SHA-256(nonce || value)` using the Web Crypto API
4. Only the **commitment hash** is sent to the server — the nonce and value stay in browser memory
5. The local dice face is shown to the player immediately as confirmation

### 5. Reveal Phase

Once both commitments are stored, the server automatically transitions to `revealing`. The frontend detects this on the next poll and sends the actual nonce and value to `POST /api/game/{id}/reveal/`.

The server then:

1. Recomputes `SHA-256(nonce || value)` from the submitted reveal
2. Compares it to the stored commitment
3. Rejects the reveal if they do not match (would mean the player tampered with their value)
4. Once both reveals are verified, compares the two values and records the winner

### 6. Result

The game view shows both dice side by side with a Win / Lose / Draw banner.

---

## The Bit Commitment Protocol

A **bit commitment scheme** lets one party commit to a value without revealing it, and then prove later that their revealed value matches what they committed to.

### Construction

```
commitment = SHA-256(nonce || value)
```

- **nonce** — a 256-bit random secret, unique per roll, generated in the browser
- **value** — the dice result (1–6)
- **||** — string concatenation before hashing
- **SHA-256** — a one-way cryptographic hash function

### Protocol Steps

```
Player A (browser)               Server               Player B (browser)
─────────────────               ──────               ─────────────────
roll dice → value_A
generate nonce_A
commit_A = H(nonce_A || value_A)
                     ──commit_A──▶
                                                      roll dice → value_B
                                                      generate nonce_B
                                                      commit_B = H(nonce_B || value_B)
                                 ◀──commit_B──
                    (both stored; state → revealing)

send (nonce_A, value_A)
                     ──reveal──▶
                     verify: H(nonce_A || value_A) == commit_A  ✓
                                                      send (nonce_B, value_B)
                                 ◀──reveal──
                                 verify: H(nonce_B || value_B) == commit_B  ✓

                     compare value_A vs value_B → winner
```

### Security Properties

| Property | Guarantee |
|----------|-----------|
| **Hiding** | The commitment hash reveals nothing about the dice value. SHA-256 is a one-way function; an observer cannot reverse it to learn the value. |
| **Binding** | Once committed, a player cannot change their value. Finding a different (nonce', value') pair that produces the same SHA-256 hash is computationally infeasible (collision resistance). |

---

## Why This Is Fair

Without a commitment scheme, a dishonest player could:

- Roll first, see the opponent's roll, and then pick a better value
- Claim they rolled a 6 when they actually rolled a 1

The commitment scheme prevents both attacks:

1. **Cannot change after seeing opponent** — the hash is sent before either value is revealed. By the time reveals happen, both values are already locked in.
2. **Cannot lie about the value** — the server rejects any reveal where `SHA-256(nonce || claimed_value) ≠ stored_commitment`.
3. **Server cannot cheat** — the nonce is generated in the browser and never sent to the server until the reveal phase. The server has no way to use the committed hash to learn the value before both players reveal.

The nonce is essential: without it, an attacker could precompute `SHA-256("1")` through `SHA-256("6")` and reverse the commitment instantly. The random 256-bit nonce makes this lookup attack impossible.

---

## API Reference

All game endpoints require a JWT `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Create account |
| `POST` | `/api/auth/login/` | Login, receive JWT pair |
| `POST` | `/api/auth/logout/` | Blacklist tokens |
| `GET`  | `/api/auth/me/` | Current user info |
| `POST` | `/api/token/refresh/` | Refresh access token |

### Game

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/game/heartbeat/` | Mark yourself as online |
| `GET`  | `/api/game/online-users/` | List players online in the last 30s |
| `GET`  | `/api/game/` | Your active and recent games |
| `POST` | `/api/game/` | Challenge a player `{ "opponent_id": 42 }` |
| `GET`  | `/api/game/{id}/` | Game detail |
| `POST` | `/api/game/{id}/accept/` | Accept a pending challenge |
| `POST` | `/api/game/{id}/decline/` | Decline a pending challenge |
| `POST` | `/api/game/{id}/commit/` | Submit commitment `{ "commitment": "<sha256hex>" }` |
| `POST` | `/api/game/{id}/reveal/` | Submit reveal `{ "nonce": "...", "value": 4 }` |

### Game States

```
pending ──accept──▶ committing ──both committed──▶ revealing ──both revealed──▶ finished
       └──decline──▶ declined
```

---

## Authentication

The app uses **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`:

- **Access token** — short-lived (30 minutes), sent as `Authorization: Bearer <token>` on every request
- **Refresh token** — long-lived (7 days), used to obtain a new access token when the current one expires
- **Token blacklisting** — logout blacklists both tokens so they cannot be reused even before expiry

The frontend stores tokens in `localStorage` and the `authFetch` helper automatically retries any 401 response by refreshing the access token before giving up.

---

## Local Development

### Requirements

- Python 3.12+
- Node.js 18+
- PostgreSQL (or use Docker just for the DB)

### Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r server/requirements.txt

# Copy and edit environment variables
cp .env.example .env

# Run migrations
cd server
python manage.py migrate

# Start the API
python manage.py runserver
```

### Frontend

```bash
cd server/frontend
npm install
npm run dev
```

The Vite dev server starts on http://localhost:5173 and proxies `/api/*` to `http://localhost:8000`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | (dev key) | Django secret key — change in production |
| `DEBUG` | `True` | Set to `False` in production |
| `POSTGRES_DB` | `fairexchange` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_HOST` | `db` | Database host |

---

## Testing

```bash
# Django tests
cd server
python manage.py test

# With coverage
coverage run manage.py test
coverage html
# open htmlcov/index.html
```
