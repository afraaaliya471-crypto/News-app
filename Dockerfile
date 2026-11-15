# Runtime only: Node, Python, Chromium libs, PM2.
# App code is mounted by docker-compose, not copied in.

FROM node:20-bookworm-slim

# Chromium + the libraries it needs. puppeteer-core does not download a browser.
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
