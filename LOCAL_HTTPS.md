# Local HTTPS Setup

This project uses direct local TLS in Django and Vite for HTTPS development.

## What changed

- Django serves HTTPS directly on `https://localhost:8000`
- Vite serves HTTPS directly on `https://localhost:5173`
- Both services use the same locally generated certificates from `mkcert`

## One-time setup per machine

1. Install `mkcert`

Windows:

```powershell
winget install FiloSottile.mkcert
```

Linux:

```bash
sudo apt install mkcert libnss3-tools
```

2. Install the local CA into your OS/browser trust store

```bash
mkcert -install
```

3. Generate local certificates from the project root

```bash
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

## Start the stack

```bash
docker compose up -d --build
```

Then open:

- `https://localhost:5173`
- `https://localhost:8000/api/docs/`
- `https://localhost:8000/admin/`

## Verify

```bash
docker compose ps
docker compose logs -f server
docker compose logs -f frontend
```

You should see `db`, `server`, and `frontend` running.

## Notes

- Django terminates TLS directly with `uvicorn`.
- Vite also runs over HTTPS so the local app is fully served with TLS.
- The frontend proxies `/api` and `/admin` to Django over HTTPS.
- If port `5173` or `8000` is already in use, stop the conflicting service before starting Docker Compose.
