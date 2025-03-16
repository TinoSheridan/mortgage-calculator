# Mortgage Calculator Deployment Guide

This guide provides instructions for deploying the Mortgage Calculator application in a production environment.

## Prerequisites

- Ubuntu 20.04 LTS or newer
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx
- Let's Encrypt (for SSL certificates)

## Installation Steps

1. **System Packages**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-venv python3-dev postgresql postgresql-contrib nginx redis-server
```

2. **Create Application User and Directory**

```bash
# Create application user
sudo useradd -m -s /bin/bash mortgage_calc

# Create application directory
sudo mkdir -p /var/www/mortgage_calc
sudo chown mortgage_calc:www-data /var/www/mortgage_calc
```

3. **PostgreSQL Setup**

```bash
# Create database and user
sudo -u postgres psql
postgres=# CREATE DATABASE mortgage_calc;
postgres=# CREATE USER mortgage_calc WITH PASSWORD 'secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE mortgage_calc TO mortgage_calc;
postgres=# \q
```

4. **Application Setup**

```bash
# Clone repository
cd /var/www/mortgage_calc
git clone [repository_url] .

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
sudo mkdir /etc/mortgage_calc
sudo cp .env.example /etc/mortgage_calc/environment
sudo chown -R mortgage_calc:www-data /etc/mortgage_calc
sudo chmod 640 /etc/mortgage_calc/environment
```

5. **SSL Certificate Setup**

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d mortgagecalc.example.com

# Generate DH parameters
sudo ./scripts/generate_ssl.sh
```

6. **Nginx Configuration**

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/mortgage_calc
sudo ln -s /etc/nginx/sites-available/mortgage_calc /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

7. **Systemd Service Setup**

```bash
# Copy service file
sudo cp mortgage_calc.service /etc/systemd/system/

# Start service
sudo systemctl daemon-reload
sudo systemctl enable mortgage_calc
sudo systemctl start mortgage_calc
```

8. **Backup Setup**

```bash
# Create backup directory
sudo mkdir -p /var/backups/mortgage_calc
sudo chown mortgage_calc:www-data /var/backups/mortgage_calc

# Set up cron job for backups
(crontab -l 2>/dev/null; echo "0 2 * * * /var/www/mortgage_calc/scripts/backup.py") | crontab -
```

## Security Measures

1. **Firewall Configuration**

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **File Permissions**

```bash
# Secure sensitive files
sudo chmod 600 /etc/mortgage_calc/environment
sudo chmod 640 mortgage_config.json
sudo chmod -R 750 scripts/
```

3. **SELinux Configuration (if enabled)**

```bash
sudo semanage fcontext -a -t httpd_sys_content_t "/var/www/mortgage_calc(/.*)?"
sudo restorecon -Rv /var/www/mortgage_calc
```

## Monitoring Setup

1. **Prometheus & Grafana**

The application exports metrics at `/metrics`. Set up Prometheus to scrape these metrics and Grafana for visualization.

2. **Logging**

Logs are stored in:
- Application logs: `/var/log/mortgage_calc/app.log`
- Access logs: `/var/log/mortgage_calc/access.log`
- Error logs: `/var/log/mortgage_calc/error.log`

## Maintenance

1. **Backup Verification**

```bash
# Verify backup integrity
sudo -u mortgage_calc /var/www/mortgage_calc/scripts/backup.py --verify
```

2. **SSL Certificate Renewal**

```bash
# Certificates will auto-renew, but you can test with:
sudo certbot renew --dry-run
```

3. **Log Rotation**

Logrotate configuration is included and will handle log rotation automatically.

## Troubleshooting

1. **Check Application Status**

```bash
sudo systemctl status mortgage_calc
sudo journalctl -u mortgage_calc -f
```

2. **Check Nginx Status**

```bash
sudo systemctl status nginx
sudo nginx -t
```

3. **Check SSL Certificate**

```bash
sudo certbot certificates
```

## Security Contacts

- For security issues: security@example.com
- For urgent issues: +1-XXX-XXX-XXXX

## Additional Resources

- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
