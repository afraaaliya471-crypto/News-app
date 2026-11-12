# UAE & Saudi Construction News Monitor

Tracks construction-industry news across the UAE and Saudi Arabia, filters it down to genuine contract/project awards using an LLM (not just keyword matching), and posts the real ones to a WhatsApp group automatically.

The problem this solves: a plain keyword search for "awarded" or "contract" across construction news pulls in a lot of noise — market commentary, unrelated tech deals, "exploring a deal" stories that never close. The LLM step is what filters that down to things that actually happened.

## How it works

1. **Fetch** — polls Google News RSS for a fixed list of trusted publishers (`sources.py` has the exact list — UAE and Saudi dailies, construction trade press, a few regional/real-estate outlets). Runs every 5 minutes.
2. **Keyword gate** — a cheap first pass checks for construction-related and award-related wording, and tags the country (UAE or Saudi Arabia) from city/project-name keywords.
3. **LLM judgment** — every headline that survives the keyword gate goes to an LLM (OpenAI or Gemini), which is deliberately strict: it has to be an actual signed/awarded contract or project, for a real construction/infrastructure project, in one of the two countries. Market stats, "in talks" stories, and anything non-construction get rejected, with a stated reason you can see on the dashboard.
4. **Cross-publisher duplicate check** — the same contract often gets reported by two or three different outlets with different headlines. Before sending, the system checks whether this is the same underlying story as something already sent today (semantically, not just matching words), so the group doesn't get the same deal twice.
5. **Send** — approved, fresh (today's date), non-duplicate articles get queued and posted to the configured WhatsApp group automatically, paced a bit apart rather than all at once.

Every stage is visible on the dashboard, so you can see not just what got sent, but what got rejected and why.

## The dashboard tabs

- **Search** — manual search across all sources, any date range.
- **Extracted** — raw headlines that passed the keyword gate, before the LLM looks at them.
- **LLM Picked** — every headline the LLM judged, with its keep/reject decision and reason.
- **Live** — today's approved articles, with their current send status.
- **News Log** — discovery history (everything ever found, sent or not).
- **Send Log** — what was actually sent to WhatsApp, or why a send failed.
- **Connect WhatsApp** — bot connection status, QR code for linking a number, group selection.

## Running it

**Dependencies:** Python 3.9+, Node.js 20+, a spare WhatsApp number (not your personal one — see the risk note below), and an OpenAI or Gemini API key.

```bash
# Python side
python -m venv .venv
.venv\Scripts\activate          # .venv/bin/activate on Linux/macOS
pip install -r requirements.txt

# Node side
npm install
```

Create a `.env` file in the project root (never committed — see `.gitignore`):
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
(or `GEMINI_API_KEY` / `GEMINI_MODEL` instead, if you'd rather use Gemini.)

Then run both processes:
```bash
# Terminal 1
node whatsapp_selfhosted.js
# scan the QR code with your spare number, or use the Connect WhatsApp tab

# Terminal 2
python app.py
# open http://localhost:5050
```

`ecosystem.config.js` is there if you'd rather run both under PM2 locally instead of two terminals (`pm2 start ecosystem.config.js`).

## Production deployment (Docker, on a shared box)

The live deployment runs in Docker, specifically so it can share a box with other, unrelated production systems without any risk of interfering with them. The key points:

- `Dockerfile` builds the runtime only (Node, Python, Chromium's system libraries). The actual code is bind-mounted from the host (`docker-compose.yml`), so a `git pull` on the host takes effect on the next restart without rebuilding the image.
- The dashboard port is published to `127.0.0.1` only — never reachable from outside the box itself. External access goes through a separate tunnel (ngrok) running on the host, not through an exposed port.
- `mem_limit`/`cpus` in `docker-compose.yml` cap what the container can ever consume, so nothing it does can starve whatever else is running on the same box.
- `ecosystem.docker.config.js` is the PM2 config actually used inside the container — it's a different file from the local one above because the container has a few container-specific needs (the Python interpreter path, the Chromium binary path, the bot's restart schedule).

Deploying an update:
```bash
cd ~/NEWSAPP && git pull
sudo docker compose up -d --build
```

One-time setup on a fresh box (before the first `docker compose up`), since the image doesn't bundle `node_modules`/the Python venv:
```bash
docker compose run --rm newsapp bash -c "npm install && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
```

## Keeping the WhatsApp bot alive

This is the part that actually needs explaining, because it took real incidents to get right. The WhatsApp bot runs a headless Chromium browser (via `whatsapp-web.js`/Puppeteer) to drive WhatsApp Web — and after enough continuous uptime, that browser page can quietly stop responding to commands while the Node process itself keeps running and still reports "ready." This happened twice in production (after 22 days uptime, then again after 9 more) before it was understood: sends would just time out, repeatedly, with no crash and no obvious error anywhere else.

Three things now guard against this, layered so no single one has to be perfect:

1. **Scheduled restart** — the bot process restarts every 3 days regardless (`ecosystem.docker.config.js`, `cron_restart`), which keeps it well under the uptime where this has ever been observed to happen. It reconnects from the saved session automatically — no QR rescan needed.
2. **Reactive restart** — if 5 send attempts in a row fail, `app.py` restarts the bot process immediately rather than waiting for the schedule (`_note_send_failure`, `MAX_SEND_ATTEMPTS`).
3. **Independent health probe** — reactive restart #2 only notices a problem while something is actually being sent. During a quiet stretch with nothing queued, nothing would ever trigger it — so there's also a standalone check every 10 minutes (`bot_health_loop`) that pokes the browser page directly, regardless of whether anything's being sent, and feeds into the same restart logic.

All three share one failure counter and a 3-minute cooldown between restarts, so this can't turn into a restart loop.

If you ever need to fix this by hand: `docker exec newsapp pm2 restart newsapp-whatsapp`. If that alone doesn't work and the logs show `process_singleton_posix.cc` / "profile appears to be in use," Chromium left a stale lock file behind from an unclean shutdown — clear it and retry:
```bash
docker exec newsapp pm2 stop newsapp-whatsapp
docker exec newsapp find /app/.whatsapp-session-data -iname "Singleton*" -delete
docker exec newsapp pm2 restart newsapp-whatsapp
```

## Data files and retention

Everything the app tracks lives in plain JSON files next to the code (not a database — at this scale, a database would be more infrastructure than the problem needs). Two of them are capped so they can't grow forever:

- `whatsapp_log.json` (Send Log) — keeps the most recent 200 "sent" and 200 "failed" entries, tracked independently so a bad day of failures can't crowd out real send history.
- `news_log.json` (News Log) — keeps the most recent 200 discovered articles.

The cap lives in `store.py` (`MAX_SENT_LOG_ENTRIES`, `MAX_FAILED_LOG_ENTRIES`, `MAX_NEWS_LOG_ENTRIES`) if it ever needs adjusting.

A failed send is capped at 5 retry attempts (`MAX_SEND_ATTEMPTS` in `app.py`) before the system gives up on that one article and moves on — otherwise a single stuck article can retry forever and flood the Send Log (this happened once: one article, retried every ~60 seconds for 13 hours straight, before anyone noticed).

## Known risk that no code can fix

This uses `whatsapp-web.js`, an unofficial library that automates WhatsApp Web — there's no official WhatsApp Business API involved. That means there's a standing, low-but-real risk that WhatsApp could restrict or log out the linked number if it looks automated. If that happens, no restart fixes it — it needs a human to open the Connect WhatsApp tab and scan a fresh QR code with a (possibly new) number. Using a spare number rather than anyone's personal one is the main mitigation; there isn't a way to eliminate the risk entirely while using this approach.

## Troubleshooting

- **LLM rejecting everything / "No evaluations yet"**: check `.env` has a valid API key. The LLM Picked tab shows every rejection reason — if good articles are being dropped, the prompt in `llm_judge.py` (`SYSTEM_PROMPT`) may need loosening; if bad ones are getting through, tighten it the same way.
- **"WhatsApp bot is not ready"**: check `docker exec newsapp pm2 status` — if the process just restarted, give it 30-60 seconds to relaunch Chromium and reconnect before assuming something's wrong.
- **Live feed stuck showing "waiting" on an article that never sends**: check the Send Log for something very similar already sent — the duplicate check (`titles_are_same_story` in `store.py`) sometimes needs a specific case added to its exclusion list if two genuinely different stories keep sharing enough generic wording to look alike.
- **Nothing showing up at all**: normal on a quiet news day or early morning before publishers have posted much — check the Extracted tab to see if anything's even being found before assuming the pipeline is broken.
