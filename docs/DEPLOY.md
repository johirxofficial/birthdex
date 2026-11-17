# Deployment guide

BirthDex is a small Flask app with one external dependency: outbound HTTPS to
`everify.bdris.gov.bd`. It needs no database, no disk writes and no scheduled
jobs.

---

## 0. Install as a package (any OS)

```bash
pipx install git+https://github.com/johirxofficial/birthdex.git   # isolated CLI install
# or
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: . .venv/bin/activate
pip install "git+https://github.com/johirxofficial/birthdex.git"
```

Then start it anywhere with the built-in Waitress server:

```bash
birthdex --host 0.0.0.0 --port 5002 --threads 8
```

The same command exists as `python -m birthdex` and, in a source checkout, as
`python app.py`.

---

## 1. Local development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: . .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- UI: <http://localhost:5002>
- Health: <http://localhost:5002/health>

`run.bat` (Windows) and `run.sh` (Linux/macOS) do this automatically, including
the virtual environment.

---

## 2. Local network (LAN)

The default bind address is `0.0.0.0`, so other devices can already reach the
machine.

1. Find the host IP: `ipconfig` (Windows) or `ip addr` (Linux).
2. Open `http://<host-ip>:5002` from another device.
3. Allow the port in the firewall:
   - Windows: `netsh advfirewall firewall add rule name="BirthDex" dir=in action=allow protocol=TCP localport=5002`
   - Linux (ufw): `sudo ufw allow 5002/tcp`

Never expose port 5002 directly to the internet with the Flask development
server. Use a real WSGI server plus a reverse proxy (below).

---

## 3. Windows production (Waitress)

Waitress ships with BirthDex, so the console command is already a production
server:

```bat
birthdex --host 0.0.0.0 --port 5002 --threads 8
```

Keep it running with **NSSM** or **Task Scheduler** ("At startup", run the
command above from the project folder). Example with NSSM:

```bat
nssm install BirthDex "C:\Python312\Scripts\birthdex.exe" --host 0.0.0.0 --port 5002 --threads 8
nssm set BirthDex AppDirectory "C:\xampp\htdocs\birthdex"
nssm start BirthDex
```

`threads` matters: the captcha store is in-process, so one process with several
threads is the simplest correct setup.

---

## 4. Linux production (Gunicorn + Nginx)

### 4.1 Gunicorn

One process, several threads (the captcha store is in memory):

```bash
. .venv/bin/activate
pip install gunicorn
gunicorn --bind 127.0.0.1:5002 --workers 1 --threads 16 --timeout 90 app:app
```

### 4.2 systemd unit

`/etc/systemd/system/birthdex.service`:

```ini
[Unit]
Description=BirthDex verification service
After=network-online.target
Wants=network-online.target

[Service]
User=birthdex
Group=birthdex
WorkingDirectory=/opt/birthdex
Environment=PORT=5002
Environment=CAPTCHA_TTL=600
ExecStart=/opt/birthdex/.venv/bin/gunicorn --bind 127.0.0.1:5002 --workers 1 --threads 16 --timeout 90 app:app
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now birthdex
sudo systemctl status birthdex
```

### 4.3 Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name birthdex.example.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

Add TLS with `certbot --nginx -d birthdex.example.com`.

Set `PUBLIC_BASE_URL=https://birthdex.example.com` in the environment so captcha
links and the `verify_with` hint use the public address instead of the internal
one.

---

## 5. Docker

```bash
docker compose up --build -d
docker compose logs -f
```

- The image runs Gunicorn as a non-root user.
- `docker-compose.yml` maps `5002:5002` and defines a health check.
- Override settings in the `environment:` block of the compose file.

Behind an HTTPS reverse proxy, add `PUBLIC_BASE_URL` to the environment.

---

## 6. Health checks and monitoring

- `GET /health` returns `200` and a JSON body; point your monitor at it.
- Logs go to stdout/stderr. The app logs portal warnings and unexpected pages.
- `sessions.active` should stay small. A constantly growing number means
  clients request captchas and never answer them.

---

## 7. Scaling

The default store keeps pending captcha sessions in process memory (`200`
entries, `600` seconds). Therefore:

- **Do:** one process with many threads (Waitress `/threads`, Gunicorn
  `--workers 1 --threads N`).
- **Don't:** run multiple worker processes behind a load balancer — a captcha
  session created on worker A is not visible to worker B.

If you truly need horizontal scaling, implement a shared store (Redis) behind
the small `CaptchaStore` interface in `birthdex/store.py`.

---

## 8. Security checklist

- [ ] Run behind HTTPS; never expose the Flask dev server.
- [ ] Set `DEBUG=0`.
- [ ] Restrict `ALLOW_ORIGIN` to the domains that need the API.
- [ ] Rate-limit `/api/verify` at the proxy (e.g. `limit_req` in Nginx).
- [ ] Keep `CAPTCHA_CAPACITY` modest to bound memory.
- [ ] Do not log request bodies or record data.
- [ ] Keep dependencies updated (`pip list --outdated`).

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `502 Could not start a captcha session` | Portal unreachable, blocked, or changed its form | Check outbound HTTPS, retry; open an issue if the page layout changed |
| `502 unexpected page` | Portal returned an error/maintenance page | Retry later |
| `410` immediately after step 1 | Session expired (> `CAPTCHA_TTL`) or already used | Start again |
| Captcha image 404/410 | Wrong id, or the session was consumed | Use `captcha.image_url` from the latest response |
| Links point to `127.0.0.1` behind a proxy | Absolute URLs built from the internal host | Set `PUBLIC_BASE_URL` |
| Port already in use | Another instance | Change `PORT` or stop the old process |
