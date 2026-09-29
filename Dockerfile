# Dockerfile
#
# Builds the RUNTIME ENVIRONMENT only (Node, Python, the system libraries
# headless Chromium needs, and PM2). The actual application code is NOT
# copied in here - docker-compose.yml bind-mounts the real project
# directory at /app instead, so `git pull` on the host is picked up
# immediately without ever rebuilding this image, and all the JSON data
# files / the WhatsApp session live on the host filesystem (survive the
# container being recreated).

FROM node:20-bookworm-slim

# Full canonical Puppeteer/Chromium dependency list for Debian, not just the
# subset that happened to come to mind first - a missing shared library here
# fails silently as "Chromium failed to launch" with no clean fallback, so
# better to include a few extra than to be missing one.
#
# `chromium` itself (the actual browser binary) is included too - whatsapp-web.js
# depends on puppeteer-core, which unlike full "puppeteer" never downloads its
# own browser. Without this, npm install succeeds but the bot fails at runtime
# with "Could not find Chrome". PUPPETEER_EXECUTABLE_PATH (set in
# ecosystem.docker.config.js) points whatsapp_selfhosted.js at this binary.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip git ca-certificates wget \
    chromium \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgtk-3-0 \
    libdbus-1-3 libxcb1 libx11-6 libxext6 libxi6 libxtst6 libexpat1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g pm2

WORKDIR /app

CMD ["pm2-runtime", "ecosystem.docker.config.js"]
