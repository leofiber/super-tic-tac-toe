# 🚀 Super Tic-Tac-Toe Production Deployment Guide

This guide covers deploying Super Tic-Tac-Toe to production environments.

## 📋 Pre-Deployment Checklist

### Environment Variables
Set these environment variables in your production environment:

```bash
# Required
SECRET_KEY=your-super-secure-secret-key-here-change-this
FLASK_CONFIG=production

# Database (choose one)
DATABASE_URL=postgresql://user:password@host:port/dbname  # PostgreSQL (recommended)
DATABASE_URL=mysql://user:password@host:port/dbname       # MySQL
DATABASE_URL=sqlite:///super_tictactoe.db                 # SQLite (not recommended for production)

# Optional: Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking
```

### Security Checklist
- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Set up proper database with backups
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Remove test accounts from database

## 🏗️ Deployment Options

### Option 1: Heroku Deployment

1. **Install Heroku CLI** and login:
   ```bash
   heroku login
   ```

2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL addon**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-super-secure-key
   heroku config:set FLASK_CONFIG=production
   ```

5. **Create Procfile**:
   ```
   web: gunicorn --worker-class gevent --workers 1 --worker-connections 1000 --bind 0.0.0.0:$PORT run:app
   ```

6. **Deploy**:
   ```bash
   git push heroku main
   ```

7. **Initialize database**:
   ```bash
   heroku run python tests/init_db.py
   ```

### Option 2: DigitalOcean App Platform

1. **Connect your GitHub repo** to DigitalOcean App Platform
2. **Configure build settings**:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn --worker-class gevent --workers 1 --worker-connections 1000 --bind 0.0.0.0:$PORT run:app`
3. **Add environment variables** in the dashboard
4. **Add PostgreSQL database** component
5. **Deploy**

### Option 3: VPS/Server Deployment

1. **Server setup** (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib
   ```

2. **Create application user**:
   ```bash
   sudo adduser supertictactoe
   sudo usermod -aG sudo supertictactoe
   ```

3. **Clone and setup application**:
   ```bash
   cd /home/supertictactoe
   git clone https://github.com/yourusername/super-tic-tac-toe.git
   cd super-tic-tac-toe
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Setup PostgreSQL**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE supertictactoe;
   CREATE USER supertictactoe WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE supertictactoe TO supertictactoe;
   \q
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

6. **Setup systemd service** (`/etc/systemd/system/supertictactoe.service`):
   ```ini
   [Unit]
   Description=Super Tic-Tac-Toe
   After=network.target

   [Service]
   User=supertictactoe
   WorkingDirectory=/home/supertictactoe/super-tic-tac-toe
   Environment=PATH=/home/supertictactoe/super-tic-tac-toe/venv/bin
   ExecStart=/home/supertictactoe/super-tic-tac-toe/venv/bin/gunicorn --worker-class gevent --workers 3 --worker-connections 1000 --bind unix:supertictactoe.sock -m 007 run:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Setup Nginx** (`/etc/nginx/sites-available/supertictactoe`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           include proxy_params;
           proxy_pass http://unix:/home/supertictactoe/super-tic-tac-toe/supertictactoe.sock;
       }

       location /socket.io {
           include proxy_params;
           proxy_http_version 1.1;
           proxy_buffering off;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "Upgrade";
           proxy_pass http://unix:/home/supertictactoe/super-tic-tac-toe/supertictactoe.sock;
       }
   }
   ```

8. **Enable and start services**:
   ```bash
   sudo systemctl enable supertictactoe
   sudo systemctl start supertictactoe
   sudo ln -s /etc/nginx/sites-available/supertictactoe /etc/nginx/sites-enabled
   sudo systemctl restart nginx
   ```

## 🔒 Security Configuration

### SSL/TLS Setup (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Firewall Setup
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 📊 Database Migration

### From Development to Production
```python
# In production environment
python tests/init_db.py  # Only for initial setup
```

### Backup Strategy
```bash
# PostgreSQL backup
pg_dump -h localhost -U supertictactoe supertictactoe > backup.sql

# Restore
psql -h localhost -U supertictactoe supertictactoe < backup.sql
```

## 📈 Monitoring and Maintenance

### Log Monitoring
- Application logs: Check systemd journal with `journalctl -u supertictactoe`
- Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

### Performance Monitoring
- Use tools like New Relic, Datadog, or Sentry for APM
- Monitor database performance
- Set up uptime monitoring

### Regular Maintenance
- Keep dependencies updated
- Monitor disk space and database size
- Regular database backups
- Security updates for the server

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check DATABASE_URL format
   - Verify database credentials
   - Ensure database server is running

2. **WebSocket Issues**
   - Verify Nginx WebSocket proxy configuration
   - Check firewall rules
   - Ensure gevent is installed

3. **Static Files Issues**
   - Configure Nginx to serve static files directly
   - Check file permissions

4. **Memory Issues**
   - Monitor memory usage
   - Adjust worker count based on available RAM
   - Consider adding swap space

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify environment variables
3. Test database connectivity
4. Check service status

Remember to remove test accounts and change default passwords before going live!
