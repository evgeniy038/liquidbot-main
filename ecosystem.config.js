module.exports = {
  apps: [
    {
      name: 'discord-bot',
      script: 'main.py',
      interpreter: './venv/bin/python',
      cwd: '/root/liquidbot',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'backend',
      script: './venv/bin/python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
      cwd: '/root/liquidbot/backend',
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'frontend',
      script: 'npm',
      args: 'run dev -- --host 0.0.0.0 --port 5173',
      cwd: '/root/liquidbot/liquidweb',
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'development'
      }
    }
  ]
};
