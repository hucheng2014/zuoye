# duomotai browser container

Local noVNC browser container for port `6085`.

## Run

```bash
docker compose up -d --build
```

Open:

- noVNC: http://127.0.0.1:6085/vnc.html
- CDP proxy: http://127.0.0.1:9239/json/version

The host bindings default to `127.0.0.1` so VNC and DevTools are not exposed to the LAN. Change `.env` only if you intentionally want different bindings.

This container does not include browser fingerprint spoofing or anti-detection scripts.
