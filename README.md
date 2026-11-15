# UAE & Saudi Construction News Monitor

Fetches construction news from UAE and Saudi publishers, keeps only real project/contract awards, and posts those to a WhatsApp group.

Keyword search alone is too noisy (market stats, "in talks", unrelated deals). An LLM judges each headline and the dashboard shows what was kept, dropped, and sent.

## How it works

1. **Fetch** — Google News RSS for the publishers in `sources.py`, every 5 minutes.
2. **Keyword gate** — construction wording + UAE/KSA place names.
3. **LLM** — keep only a real award, appointment, or named project completion. Rejections show a reason on the dashboard.
4. **Duplicates** — same story from two outlets is sent once.
5. **Send** — today's approved items go to the WhatsApp group, paced a few seconds apart.

## Dashboard tabs

- **Search** — manual lookup, any date range
- **Extracted** — after keywords, before the LLM
- **LLM Picked** — keep/drop with reasons
- **Live** — today's approved stories
- **News Log** — everything found
- **Send Log** — what went to WhatsApp (or failed)
- **Connect WhatsApp** — QR, status, group

## Run locally

Python 3.9+, Node 20+, an OpenAI or Gemini key, and a spare WhatsApp number (not a personal one).

```bash
python -m venv .venv
.venv\Scripts\activate          # .venv/bin/activate on Linux/macOS
pip install -r requirements.txt
npm install
```

`.env` (not committed):
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Or `GEMINI_API_KEY` / `GEMINI_MODEL`.

```bash
# Terminal 1
node whatsapp_selfhosted.js
# scan the QR, or use Connect WhatsApp

# Terminal 2
python app.py
# http://localhost:5050
```

Local PM2: `pm2 start ecosystem.config.js`.

## Docker (production)

Code is mounted into the container. `git pull` on the host, then restart. Port 5050 is localhost only; a tunnel on the host is how people reach the UI.

```bash
# first time
docker compose run --rm newsapp bash -c "npm install && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"

cd ~/NEWSAPP && git pull
sudo docker compose up -d --build
```

## WhatsApp bot staying up

Headless Chrome can freeze while Node still says "ready". Sends then time out with no crash.

- Restart the bot every 3 days (`cron_restart` in `ecosystem.docker.config.js`)
- Restart immediately after 5 failed sends in a row
- Health check every 10 minutes even when the queue is empty

Manual restart: `docker exec newsapp pm2 restart newsapp-whatsapp`

If logs mention a Chromium profile already in use:
```bash
docker exec newsapp pm2 stop newsapp-whatsapp
docker exec newsapp find /app/.whatsapp-session-data -iname "Singleton*" -delete
docker exec newsapp pm2 restart newsapp-whatsapp
```

## Data files

JSON next to the code, not a database.

- Send log: last 200 sent + 200 failed
- News log: last 200 discovered
- One article: max 5 send attempts

Caps are in `store.py`.

## WhatsApp risk

This uses unofficial WhatsApp Web automation, not the Business API. WhatsApp can log the number out. If that happens, scan a new QR. Use a spare SIM.

## Troubleshooting

- Everything rejected / no evaluations: check `.env`. Reasons are on LLM Picked. Adjust `SYSTEM_PROMPT` in `llm_judge.py` if it is too tight or too loose.
- Bot not ready: `docker exec newsapp pm2 status`, then wait 30–60 seconds after a restart.
- Live stuck on "waiting": check Send Log for a similar title already sent.
- Empty Live: check Extracted first. Quiet mornings are normal.
