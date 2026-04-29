# 🚀 GenAI Impact & Productivity Analyzer — Deployment Guide

This guide covers deploying GIPA on an Ubuntu server using Django, uWSGI, Nginx, and either SQLite (dev) or PostgreSQL (production).

> **For research demo purposes**, the local development server (`runserver`) is perfectly sufficient — see [Local Setup in README.md](README.md#-local-setup).

---

## 📋 Prerequisites

- Ubuntu 20.04+ server with sudo privileges
- Domain name pointing to your server (optional but recommended)
- At least 2GB RAM and 20GB storage
- Python 3.10+
- Basic knowledge of Linux command line

---

## 🛠️ Quick Start (Local Development)

```bash
# Clone the repository
git clone https://github.com/BellowAverage/ProgrammerProductivityMeasurement.git
cd "ProgrammerProductivityMeasurement"

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Apply migrations (includes A/B experiment tables)
cd fds_webapp
python manage.py migrate

# Create the static directory (avoids W004 warning)
mkdir -p static

# Start development server
python manage.py runserver
```

App available at: **http://127.0.0.1:8000**
A/B Experiment: **http://127.0.0.1:8000/ab-experiment/new/**

---

## 🔧 Production Deployment (Ubuntu Server)

### Step 1: System Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx \
    git curl wget unzip \
    build-essential libpq-dev libssl-dev libffi-dev \
    certbot python3-certbot-nginx
```

### Step 2: Database Setup (PostgreSQL)

```bash
sudo -u postgres psql

-- In PostgreSQL shell:
CREATE DATABASE gipa_db;
CREATE USER gipa_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE gipa_user SET client_encoding TO 'utf8';
ALTER ROLE gipa_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gipa_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE gipa_db TO gipa_user;
\q
```

### Step 3: Application Setup

```bash
# Create project directory
sudo mkdir -p /var/www/gipa
sudo chown $USER:$USER /var/www/gipa

# Clone repository
git clone https://github.com/BellowAverage/ProgrammerProductivityMeasurement.git /var/www/gipa
cd /var/www/gipa/fds_webapp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration

Create a `.env` file inside `fds_webapp/fds_webapp/`:

```env
SECRET_KEY=your-super-secret-django-key-replace-this
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database (switch from SQLite to PostgreSQL for production)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=gipa_db
DB_USER=gipa_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Email (optional — used for user registration verification)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

> **Note:** The current `settings.py` uses SQLite by default. For production, update the `DATABASES` dictionary in `settings.py` to use the PostgreSQL credentials above.

### Step 5: Django Setup

```bash
# Apply all migrations (includes ABExperiment and ABDeveloperScore tables)
python manage.py migrate

# Create an admin superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create the media directory for uploaded CSVs
mkdir -p media/ab_experiments
```

### Step 6: uWSGI Configuration

Create `/var/www/gipa/uwsgi.ini`:

```ini
[uwsgi]
project = gipa
base = /var/www/gipa

chdir = %(base)/fds_webapp
module = fds_webapp.wsgi:application

master = true
processes = 4
threads = 2

socket = %(base)/gipa.sock
chmod-socket = 660
vacuum = true

die-on-term = true

logto = /var/log/uwsgi/gipa.log
```

```bash
# Install systemd service
sudo nano /etc/systemd/system/gipa.service
```

Paste:

```ini
[Unit]
Description=GenAI Impact & Productivity Analyzer (GIPA) uWSGI
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/gipa/fds_webapp
Environment="PATH=/var/www/gipa/.venv/bin"
ExecStart=/var/www/gipa/.venv/bin/uwsgi --ini /var/www/gipa/uwsgi.ini

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gipa
sudo systemctl start gipa
sudo systemctl status gipa
```

### Step 7: Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/gipa
```

Paste:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /var/www/gipa/fds_webapp;
    }

    location /media/ {
        root /var/www/gipa/fds_webapp;
    }

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/var/www/gipa/gipa.sock;
    }

    # Increase upload size limit for CSV files
    client_max_body_size 50M;
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/gipa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run
```

### Step 9: File Permissions

```bash
sudo chown -R www-data:www-data /var/www/gipa
sudo chmod -R 755 /var/www/gipa
sudo chmod -R 775 /var/www/gipa/fds_webapp/media
sudo mkdir -p /var/log/uwsgi
sudo chown www-data:www-data /var/log/uwsgi
```

---

## 🔍 Post-Deployment Verification

```bash
# Check all services
sudo systemctl status gipa
sudo systemctl status nginx
sudo systemctl status postgresql

# Check application log
sudo tail -f /var/log/uwsgi/gipa.log
sudo tail -f /var/log/nginx/error.log
```

**Test these URLs after deployment:**

| URL | Expected Result |
|-----|----------------|
| `https://your-domain.com/` | Home page loads |
| `https://your-domain.com/ab-experiment/new/` | A/B upload form (no login needed) |
| `https://your-domain.com/analyses/` | Public analyses list |
| `https://your-domain.com/admin/` | Django admin panel |

---

## 🔧 Maintenance

### Update Application

```bash
cd /var/www/gipa
git pull origin main
cd fds_webapp
source ../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate        # picks up any new model changes
python manage.py collectstatic --noinput
sudo systemctl restart gipa
```

### Important: New Database Tables (A/B Feature)

The A/B experiment feature added two new tables via migration `0004_add_abexperiment`. If updating an existing deployment, always run:

```bash
python manage.py migrate dev_productivity
```

This creates:
- `dev_productivity_abexperiment` — experiment metadata and group aggregate stats
- `dev_productivity_abdeveloperscore` — per-developer scores per group

### Backup

```bash
# SQLite (development)
cp fds_webapp/db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# PostgreSQL (production)
sudo -u postgres pg_dump gipa_db > backups/gipa_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🚨 Troubleshooting

| Problem | Fix |
|---------|-----|
| `502 Bad Gateway` | `sudo systemctl status gipa` — check uWSGI is running |
| Static files not loading | `python manage.py collectstatic` then restart Nginx |
| `staticfiles.W004` warning | `mkdir -p fds_webapp/static` |
| A/B experiment stuck at "running" | Check `gipa.log` for Python traceback in background thread |
| CSV upload fails validation | Verify CSV has all 13 required columns (see README schema) |
| `fds_algorithm` import errors | Ensure you are running from inside `fds_webapp/` with the venv active |

---

## 🔐 Security Checklist

- [ ] Replaced default `SECRET_KEY` in settings
- [ ] Set `DEBUG=False` in production
- [ ] Configured `ALLOWED_HOSTS` to your domain only
- [ ] Set up SSL/TLS via Let's Encrypt
- [ ] Enabled UFW firewall (`ufw allow 'Nginx Full'`)
- [ ] Set strong database passwords
- [ ] `media/ab_experiments/` is not publicly browseable (Nginx serves only declared paths)
- [ ] Regular database backups scheduled

---

## ✅ Deployment Success Checklist

- [ ] `https://your-domain.com/` — Home page renders
- [ ] `https://your-domain.com/ab-experiment/new/` — Upload form renders without login
- [ ] Upload two test CSVs → experiment completes and dashboard renders
- [ ] Speed Δ% and Churn Δ% are non-zero on the dashboard
- [ ] `https://your-domain.com/admin/` — Admin panel accessible
