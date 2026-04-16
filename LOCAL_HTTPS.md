# Local HTTPS Setup

Django and Vite both serve over HTTPS locally using certificates from `mkcert`.

## One-time setup

### 1. Install mkcert

**Fedora:**

```bash
sudo dnf install nss-tools
sudo curl -L https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-linux-amd64 -o /usr/local/bin/mkcert
sudo chmod +x /usr/local/bin/mkcert
```

**Debian / Ubuntu:**

```bash
sudo apt install mkcert libnss3-tools
```

**Windows:**

```powershell
winget install FiloSottile.mkcert
```

### 2. Trust the local CA

```bash
mkcert -install
```

Restart Firefox after this if you use it.

### 3. Generate certificates

From the project root:

```bash
mkdir -p certs
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

## Run

```bash
docker compose up -d --build
```

- Frontend: `https://localhost:5173`
- API docs: `https://localhost:8000/api/docs/`
- Admin: `https://localhost:8000/admin/`

## Notes

- Django terminates TLS directly via uvicorn.
- Vite also serves over HTTPS.
- The frontend proxies `/api` and `/admin` to Django.
- If port 5173 or 8000 is in use, stop the conflicting process first.
