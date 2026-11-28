# Deploy on hexevent.mmg.uci.edu

This runbook prepares `/exons/` alongside HEXEvent and `/maxent/`. It does not
replace the existing Apache configuration. Files in `deploy/` are templates;
inspect the actual server before applying them. No server changes are automatic.

## Layout and runtime

- Code and virtual environment: `/home/hertellab/exon-conservation/`
- Private settings: `/home/hertellab/exon-conservation/.env.prod` (mode 600)
- Public assets only: `/var/www/exon-conservation/static/`
- Service: `exon-conservation.service`; logs: its systemd journal
- Proposed internal endpoint: `127.0.0.1:8502` (confirm availability first)
- Public endpoint: `https://hexevent.mmg.uci.edu/exons/`
- PostgreSQL: persistent service on this server, dedicated `exon_conservation`
  database and login; never reuse an existing application's database or role.

Django 5.2 LTS supports Python 3.10 and receives extended support through April
2028. `app/requirements.txt` pins direct and transitive runtime dependencies,
resolved for Python 3.10. Use Ubuntu-maintained Python security updates; do not
replace the server's system Python. Reassess the OS/Python support plan with the
administrator before Ubuntu standard maintenance ends. Docker remains an
optional development environment; this server setup uses systemd and a venv.

## 1. Inspect, then select the port and dependencies

Connect using the university VPN if SSH requires it:

```sh
ssh hertellab@hexevent.mmg.uci.edu
systemctl list-units --type=service --state=running --no-pager
sudo ss -lntup
free -h
df -h /
python3 --version
psql --version
sudo apache2ctl -S
sudo apache2ctl -M
sudo cat /etc/apache2/sites-available/default-ssl.conf
```

Record existing HEXEvent and MaxEnt behavior before making changes. Check
PostgreSQL version and configuration if already installed. Django 5.2 requires
PostgreSQL 14 or newer. Never upgrade an existing database server as part of this
app deployment without a separate plan. Keep MaxEnt's port 8501 untouched.
Change 8502 in both `deploy/gunicorn.conf.py` and the Apache snippet if occupied.

If packages are missing, preview only those required:

```sh
apt-get --simulate --no-install-recommends install python3-venv postgresql postgresql-contrib
```

Review upgrades/removals with the administrator, then install missing packages:

```sh
sudo env NEEDRESTART_MODE=l apt-get --no-install-recommends install python3-venv postgresql postgresql-contrib
```

Do not restart unrelated services or reboot. PostgreSQL should listen locally;
check existing settings before altering anything used by other applications.
Do not expose either PostgreSQL or port 8502 publicly.

## 2. Upload and isolate dependencies

Create `/home/hertellab/exon-conservation` on the server. From the local project
root, preview and then transfer only the required files (no `--delete`):

```sh
rsync -av --dry-run --exclude='__pycache__/' --exclude='*.pyc' --exclude='*.sqlite3' --exclude='staticfiles/' --exclude='data/extra/' app deploy docs README.md hertellab@hexevent.mmg.uci.edu:/home/hertellab/exon-conservation/
rsync -av --exclude='__pycache__/' --exclude='*.pyc' --exclude='*.sqlite3' --exclude='staticfiles/' --exclude='data/extra/' app deploy docs README.md hertellab@hexevent.mmg.uci.edu:/home/hertellab/exon-conservation/
```

Both active CSVs must be real data files, not Git LFS pointers. If deploying with
Git instead, retrieve LFS content before importing. Never transfer `.env.dev`.

On the server:

```sh
cd /home/hertellab/exon-conservation
python3 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/pip check
cp deploy/.env.prod.example .env.prod
chmod 600 .env.prod
.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

Edit `.env.prod`: supply a new key and database password. Its simple KEY=value
format is intentionally compatible with systemd and the shell commands below.
Keep secrets outside Git and Apache's public directory. The previously tracked
development key remains in Git history: replace it anywhere it was deployed;
untracking does not erase history. Coordinate any history rewrite separately.

## 3. Dedicated database and initial preparation

If the proposed role/database already exists, inspect ownership and contents
rather than recreating or overwriting it. For a new database, use an interactive
administrator session (password entry stays out of shell history):

```sh
sudo -u postgres psql
```

```sql
CREATE ROLE exon_conservation LOGIN;
\password exon_conservation
CREATE DATABASE exon_conservation OWNER exon_conservation;
\connect exon_conservation
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\quit
```

Enter the same password in `.env.prod`. The application account does not need
superuser privileges. The administrator creates the extension in advance.

Create the new static directory, owned by the application user but readable by
Apache. Do not change permissions on the application's home directory:

```sh
sudo install -d -o hertellab -g hertellab -m 755 /var/www/exon-conservation
sudo install -d -o hertellab -g hertellab -m 755 /var/www/exon-conservation/static
cd /home/hertellab/exon-conservation
set -a
. ./.env.prod
set +a
cd app
../.venv/bin/python manage.py migrate --noinput
../.venv/bin/python manage.py import_exons --assembly hg19
../.venv/bin/python manage.py import_exons --assembly hg38
../.venv/bin/python manage.py collectstatic --noinput
../.venv/bin/python manage.py check --deploy
```

Review deployment-check output. Django will warn that SSL redirection and HSTS
are not enabled in Django: HTTPS redirection and any HSTS policy belong to the
existing Apache site. Verify them there; do not change site-wide HSTS casually.
Preparation is a release step, not part of service startup. Restarting the app
must not run migrations or re-import datasets.

Run regression tests against a separate temporary PostgreSQL database. Django's
test runner creates `test_exon_conservation`; verify that name is unused first.
An administrator can temporarily grant CREATEDB to this dedicated role, run
`../.venv/bin/python manage.py test rna --noinput`, then revoke CREATEDB even if
tests fail. Never point tests at an existing app's database.

## 4. Private test before publishing

From `app/`, with the environment still loaded:

```sh
../.venv/bin/gunicorn --config ../deploy/gunicorn.conf.py exon.wsgi:application
```

On the local computer, open a second terminal:

```sh
ssh -N -L 8502:127.0.0.1:8502 hertellab@hexevent.mmg.uci.edu
```

Open `http://localhost:8502/`. Apache strips `/exons/` in production, so direct
backend requests use `/`; generated links intentionally contain `/exons/`.
For a complete private path/static check, stop Gunicorn and temporarily run:

```sh
DEBUG=true DJANGO_SCRIPT_NAME= ../.venv/bin/python manage.py runserver 127.0.0.1:8502 --noreload
```

Use the tunnel to check both assemblies, filters, columns, invalid form input,
row jumps, scrolling and complete CSV/TXT exports. This temporary development
server is loopback-only and must be stopped before installing the service.
Final prefix, HTTPS and Apache static checks happen after the scoped proxy is
installed. No authentication tests should use the insecure tunnel with
production secure cookies.

## 5. Persistent service and Apache publication

Stop the manually launched process. Return to the project root and install only the new service:

```sh
cd /home/hertellab/exon-conservation
sudo cp deploy/exon-conservation.service /etc/systemd/system/exon-conservation.service
sudo systemctl daemon-reload
sudo systemctl enable --now exon-conservation
sudo systemctl status exon-conservation --no-pager
sudo journalctl -u exon-conservation -n 50 --no-pager
```

Commands above assume the project root as working directory. Confirm the new
process binds only to 127.0.0.1. Two sync workers are an initial configuration;
check available memory and representative export workloads before adjusting.

Back up `/etc/apache2/sites-available/default-ssl.conf` to a uniquely dated file.
Confirm `proxy`, `proxy_http`, `headers`, and `alias` modules are available; enable
only missing modules as part of the reviewed Apache change. Copy the contents of
`deploy/apache-exons.conf` inside the existing HTTPS VirtualHost, before any
catch-all ProxyPass rules. Do not replace the VirtualHost. Preserve SSL settings,
HEXEvent, MaxEnt and existing HTTP-to-HTTPS redirection. No WebSockets are needed.

The static exclusion must precede the proxy mapping. Apache removes `/exons/`
when forwarding to the backend; Django's `FORCE_SCRIPT_NAME` restores it when
building URLs. Apache overwrites X-Forwarded-Proto for this location, and the
backend is loopback-only. Do not trust that header on a publicly exposed backend.

```sh
sudo apache2ctl configtest
```

Only after `Syntax OK`:

```sh
sudo systemctl reload apache2
systemctl is-active apache2
```

Verify `/exons` redirects to `/exons/`, CSS/JS load under `/exons/static/`, About
and admin redirects stay under `/exons/`, and all main workflows work over HTTPS.
Verify HEXEvent and `/maxent/` still work. Check from cellular with Wi-Fi/VPN off,
disconnect SSH, and confirm availability. Inspect memory, CPU, and app logs under
representative searches and downloads.

## Updates, backups and rollback

Before each update, save the deployed code, locked dependencies, environment,
service file and Apache configuration; restrict access to secret-bearing backups.
Use `pg_dump -Fc` with protected credentials to back up only this application's
database, plus both source CSVs. Store backups outside the web-served directory
and verify restores into a separate database.

Resolve dependency upgrades deliberately from `app/requirements.in` in an
isolated Python 3.10 environment, freeze the complete runtime set into
`app/requirements.txt`, and rerun PostgreSQL and browser checks. Do not upgrade
packages automatically on service restart. Record `python --version`,
`pip freeze`, PostgreSQL version, release commit, port and backup location.

Run preparation once for a reviewed update, then restart only
`exon-conservation.service`. If code rollback requires an older schema, restore
its compatible database backup rather than blindly reversing migrations. Restore
static files along with code. To withdraw the new route, restore the backed-up
Apache configuration, run configtest, then gracefully reload Apache. Stop/disable
only the new service. Never remove or modify the HEXEvent/MaxEnt services.
