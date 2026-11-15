// PM2 inside the container. Tunnel stays on the host, pointed at 127.0.0.1:5050.

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
        PUPPETEER_EXECUTABLE_PATH: "/usr/bin/chromium",
      },
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
      // Restart every 3 days at 2am UTC. The session froze after long uptime.
      cron_restart: "0 2 */3 * *",
    },
  ],
};
