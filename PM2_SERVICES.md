# PM2 Services Management

## Running Services

All services are managed via PM2 and configured in `ecosystem.config.js`:

1. **discord-bot** - Discord bot (port: internal)
2. **backend** - FastAPI backend (port: 8000)
3. **frontend** - Vite dev server (port: 5173)

## Service URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Backend Health: http://localhost:8000/api/health

## PM2 Commands

### View all services
```bash
pm2 list
```

### View logs
```bash
pm2 logs                    # All services
pm2 logs frontend           # Specific service
pm2 logs backend --lines 50 # Last 50 lines
```

### Restart services
```bash
pm2 restart all             # All services
pm2 restart frontend        # Specific service
pm2 restart ecosystem.config.js  # Restart from config
```

### Stop/Start services
```bash
pm2 stop all
pm2 start all
pm2 stop frontend
pm2 start frontend
```

### Delete and recreate
```bash
pm2 delete all
pm2 start ecosystem.config.js
pm2 save
```

### Monitor services
```bash
pm2 monit
```

## Auto-start on reboot

Services are configured to auto-start on system reboot via systemd.

To disable:
```bash
pm2 unstartup systemd
```

To re-enable:
```bash
pm2 startup systemd
pm2 save
```

## Troubleshooting

### Frontend not accessible
```bash
pm2 restart frontend
pm2 logs frontend --lines 20
```

### Backend errors
```bash
pm2 restart backend
pm2 logs backend --lines 20
```

### Check ports
```bash
ss -tlnp | grep -E ':(5173|8000)'
```

### Full restart
```bash
pm2 delete all
pm2 start ecosystem.config.js
pm2 save
```

## Fixed Issues

- ✅ Fixed PortfolioView.jsx import (TweetCard from correct path)
- ✅ Frontend running on port 5173 (dev mode)
- ✅ Backend running on port 8000
- ✅ All services auto-restart on failure
- ✅ Services persist across reboots
