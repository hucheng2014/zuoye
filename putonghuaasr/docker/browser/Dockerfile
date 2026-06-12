FROM mcr.microsoft.com/playwright:v1.52.0-noble

USER root

# Install VNC and noVNC dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    fluxbox \
    xterm \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Create browser profile directory
RUN mkdir -p /home/pwuser/chrome-profile && chown -R pwuser:pwuser /home/pwuser/chrome-profile

# Copy stealth extension
COPY stealth-extension /home/pwuser/stealth-extension
RUN chown -R pwuser:pwuser /home/pwuser/stealth-extension

# Copy entrypoint
COPY start-browser.sh /usr/local/bin/start-browser.sh
RUN chmod +x /usr/local/bin/start-browser.sh

USER pwuser

ENV DISPLAY=:99
ENV VNC_PASSWORD=""
ENV CDP_PORT=9222
ENV SCREEN_WIDTH=1280
ENV SCREEN_HEIGHT=720
ENV SCREEN_DEPTH=24

EXPOSE 6080 9222 9223

ENTRYPOINT ["/usr/local/bin/start-browser.sh"]
