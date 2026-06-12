FROM mcr.microsoft.com/playwright:v1.52.0-noble

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11vnc novnc websockify fluxbox socat curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/pwuser/chrome-profile && chown -R pwuser:pwuser /home/pwuser/chrome-profile

COPY stealth-extension /home/pwuser/stealth-extension
RUN chown -R pwuser:pwuser /home/pwuser/stealth-extension

COPY start-browser.sh /usr/local/bin/start-browser.sh
RUN chmod +x /usr/local/bin/start-browser.sh

USER pwuser

ENV DISPLAY=:99
ENV VNC_PASSWORD=""
ENV CDP_PORT=9222
ENV CDP_PROXY_PORT=9223
ENV SCREEN_WIDTH=1920
ENV SCREEN_HEIGHT=1080
ENV SCREEN_DEPTH=24
ENV START_URL=about:blank

EXPOSE 6080 9222 9223

ENTRYPOINT ["/usr/local/bin/start-browser.sh"]
