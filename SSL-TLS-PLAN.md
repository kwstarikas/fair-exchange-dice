# SSL/TLS Implementation Plan

## Current State

| Layer | Status |
|-------|--------|
| ngrok tunnel | HTTPS provided automatically by ngrok |
| Django → browser | Plain HTTP locally (port 8000) |
| `SECURE_SSL_REDIRECT` | Not set |
| `HSTS` | Not set |
| Secure cookies | Not set |

---

## Phase A — Django Security Headers (no certificate required)

These settings work immediately with ngrok's TLS termination and cost nothing.
ngrok terminates HTTPS before Django sees the request and forwards it with an
`X-Forwarded-Proto: https` header — which is what `SECURE_PROXY_SSL_HEADER` reads.

### Changes to `server/server/settings.py`

```python
# Add inside a `if not DEBUG:` block
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
```

**Do NOT add `SECURE_SSL_REDIRECT = True` yet** — that is only safe once Django
is running behind a real HTTPS reverse proxy (Phase C).

### Acceptance criteria

- [ ] All headers above present in production responses (verify with `curl -I`)
- [ ] Session and CSRF cookies have the `Secure` flag set
- [ ] No redirect loops in local development (`DEBUG=True` bypasses these settings)

---

## Phase B — Choose a Deployment Target

Two options. Pick one before continuing to Phase C.

### Option 1 — VPS (DigitalOcean, Hetzner, Linode)

```
Browser ──HTTPS:443──▶ Nginx (TLS termination) ──HTTP:8000──▶ Gunicorn/Django
                              ↑
                     Let's Encrypt certificate
                     (free, auto-renewed via Certbot)
```

**Pros:** Full control, cheapest long-term, standard setup.
**Cons:** You manage the server, Nginx config, and cert renewal.

Requirements:
- A domain name with an A record pointing to the server IP
- Ubuntu/Debian VPS (any provider)

### Option 2 — Platform-as-a-Service (Railway, Render, Fly.io)

```
Browser ──HTTPS──▶ Platform edge (TLS managed for you) ──▶ Django container
```

**Pros:** Zero SSL configuration — HTTPS is on by default on their subdomain.
Certs are issued and renewed automatically.
**Cons:** Less control, slightly higher cost at scale.

---

## Phase C — Production Certificate Setup (Option 1, VPS)

### 1. Point your domain

```
A record:  yourdomain.com  →  <server IP>
A record:  www.yourdomain.com  →  <server IP>
```

### 2. Install Nginx and Certbot

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### 3. Create Nginx site config

```nginx
# /etc/nginx/sites-available/fairexchange
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/fair-exchange-dice/server/static/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fairexchange /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Issue the certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will:
- Obtain a certificate from Let's Encrypt
- Automatically update the Nginx config to listen on 443
- Set up a cron job for automatic renewal

### 5. Verify auto-renewal

```bash
sudo certbot renew --dry-run
```

---

## Phase D — Django Production Settings

Once Nginx + HTTPS is confirmed working, enable the remaining hardening in
`settings.py`:

```python
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True           # redirect all HTTP → HTTPS
    SECURE_HSTS_SECONDS = 31536000       # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True           # submit to browser preload lists
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

> **Warning:** `SECURE_HSTS_PRELOAD = True` is permanent — once a domain is in
> the browser preload list, removing it takes months. Only set this when you are
> sure HTTPS will stay on forever for this domain.

### Update `ALLOWED_HOSTS`

```python
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

---

## Phase E — Frontend Build for Production

The React app is served as static files built by Vite and served by Nginx.

```bash
cd server/frontend
npm run build
# Output: server/static/frontend/
```

Django's `collectstatic` picks this up. Nginx serves `/static/` directly.

```bash
cd server
python manage.py collectstatic --no-input
```

No changes to `authFetch` or API calls — all paths are relative (`/api/...`)
and will work whether served from `localhost` or `yourdomain.com`.

---

## Checklist

### Phase A (now — works with ngrok)
- [ ] Add security headers to `settings.py` under `if not DEBUG`
- [ ] Verify headers in a production-like environment with `curl -I`

### Phase B
- [ ] Decide: VPS (Option 1) or PaaS (Option 2)
- [ ] Register/point a domain name

### Phase C (VPS only)
- [ ] Provision server
- [ ] Install Nginx + Certbot
- [ ] Configure Nginx reverse proxy
- [ ] Run `certbot --nginx` to obtain certificate
- [ ] Confirm HTTPS works in browser (green padlock)
- [ ] Confirm `certbot renew --dry-run` passes

### Phase D
- [ ] Enable `SECURE_SSL_REDIRECT` in settings
- [ ] Enable HSTS (start with `SECURE_HSTS_SECONDS = 3600`, increase after testing)
- [ ] Run Django's deployment checklist: `python manage.py check --deploy`

### Phase E
- [ ] `npm run build` produces correct output in `server/static/frontend/`
- [ ] `collectstatic` runs without errors
- [ ] Nginx serves `/static/` correctly
- [ ] Full end-to-end test over HTTPS with another browser/device
