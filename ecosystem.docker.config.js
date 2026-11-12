// ecosystem.docker.config.js
//
// PM2 config used only inside the Docker container (started via
// `pm2-runtime` as the container's own CMD). Deliberately does not include
// a tunnel entry - the tunnel keeps running on the host exactly as before,
// pointed at the container's published port (127.0.0.1:5050), unchanged.

module.exports = {
  apps: [
    {
      name: "newsapp-flask",
      script: "app.py",
      interpreter: "/app/.venv/bin/python3",
      cwd: "/app",
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
    },
    {
      name: "newsapp-whatsapp",
      script: "whatsapp_selfhosted.js",
      cwd: "/app",
      env: {
        WA_SESSION_DIR: "/app/.whatsapp-session-data",
        // puppeteer-core (whatsapp-web.js's dependency) never downloads its
        // own browser - it must be told where the Dockerfile installed one.
        PUPPETEER_EXECUTABLE_PATH: "/usr/bin/chromium",
      },
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
      // The underlying headless-browser WhatsApp Web session degrades after
      // long continuous uptime (confirmed: froze after 22 days, then again
      // after 9 more). A restart isn't free - briefly relaunches Chromium
      // from scratch, and every restart is itself a small chance of a bad
      // reconnect - so this restarts only every 3rd day, not nightly: still
      // far below both observed freeze thresholds, with a third of the
      // restart-events (and a third of the restart-risk) of a daily
      // schedule. 2am UTC (6am Gulf time), well outside business hours.
      // Reconnects from the saved session automatically, no QR scan.
      cron_restart: "0 2 */3 * *",
    },
  ],
};
