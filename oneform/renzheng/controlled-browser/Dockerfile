FROM mcr.microsoft.com/playwright:v1.52.0-noble

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      curl \
      fluxbox \
      novnc \
      socat \
      websockify \
      x11vnc \
      xvfb \
    && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=:99 \
    SCREEN_WIDTH=1920 \
    SCREEN_HEIGHT=1080 \
    SCREEN_DEPTH=24 \
    CDP_PORT=9222 \
    CDP_PROXY_PORT=9223 \
    START_URL=about:blank \
    VNC_PASSWORD=

COPY scripts/stealth-extension /home/pwuser/stealth-extension

COPY scripts/start-browser.sh /usr/local/bin/start-browser.sh
RUN chmod +x /usr/local/bin/start-browser.sh \
    && chown -R pwuser:pwuser /home/pwuser/stealth-extension \
    && mkdir -p /home/pwuser/chrome-profile \
    && chown -R pwuser:pwuser /home/pwuser/chrome-profile

USER pwuser

EXPOSE 6080 9222 9223

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
  CMD curl -sf "http://localhost:${CDP_PORT}/json/version" >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/start-browser.sh"]
