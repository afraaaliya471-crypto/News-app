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
      },
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
    },
  ],
};
