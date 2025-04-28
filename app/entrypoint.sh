#!/bin/sh
set -e

cd /app

python manage.py makemigrations
python manage.py migrate 

# 1) Wait for Postgres (if DATABASE_URL is set)
if command -v nc >/dev/null 2>&1 && [ -n "$DATABASE_URL" ]; then
  echo "Waiting for Postgres..."
  export PGHOST=$(python - <<PYCODE
import os, dj_database_url
print(dj_database_url.parse(os.environ["DATABASE_URL"])["HOST"])
PYCODE
)
  export PGPORT=$(python - <<PYCODE
import os, dj_database_url
print(dj_database_url.parse(os.environ["DATABASE_URL"])["PORT"] or 5432)
PYCODE
)
  while ! nc -z "$PGHOST" "$PGPORT"; do sleep 0.1; done
  echo "Postgres is up"
fi

# 2) Run migrations
echo "→ applying migrations"
python manage.py migrate --no-input

# 3) Seed the table (once)
TABLE_COUNT=$(printf "SELECT COUNT(*) FROM rna_exonconservation;\n" \
              | python manage.py dbshell | tr -dc '0-9')
if [ "$TABLE_COUNT" -eq 0 ]; then
  echo "→ importing data (first-time load)"
  python data/import_data.py
else
  echo "→ data present; skipping import"
fi

# 4) Collect static files once
echo "→ collecting static files"
python manage.py collectstatic --no-input --clear

# 5) Launch Gunicorn
echo "→ starting Gunicorn"
exec gunicorn exon.wsgi:application \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers 3