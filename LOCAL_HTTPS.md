# Local HTTPS Setup

This project includes a local HTTPS reverse proxy using `nginx` and generated certificates from `mkcert`.

## What gets committed

- `docker-compose.yml` wiring for the `nginx` reverse proxy
- `docker/nginx/local-https.conf`
- application settings that trust `X-Forwarded-Proto`


## One-time setup per machine

1. Install `mkcert`

```powershell
winget install FiloSottile.mkcert
```

2. Install the local CA into your OS/browser trust store

```powershell
mkcert -install
```

3. Generate local certificates from the project root

```powershell
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

## Start the stack

Set the frontend public host for secure HMR:

```powershell
$env:VITE_PUBLIC_HOST="localhost"
docker compose up -d --build
```

Then open:

- `https://localhost`
- `https://localhost/api/docs/`
- `https://localhost/admin/`

## Verify

```powershell
docker compose ps
docker compose logs -f nginx
docker compose logs -f frontend
```

You should see `db`, `server`, `frontend`, and `nginx` running.

## Notes

- The Vite dev server runs only behind `nginx`; HTTPS is terminated at `nginx`.
- The frontend is not exposed directly on `http://localhost:5173`.
- If port 80 or 443 is already in use, stop the conflicting service before starting Docker Compose.
