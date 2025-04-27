#!/bin/sh
set -e

# 1) (Optional) wait for Postgres to be ready
#    Render provides DATABASE_URL; we parse host/port via dj-database-url
if command -v nc >/dev/null 2>&1 && [ -n "$DATABASE_URL" ]; then
  echo "Waiting for Postgres..."
  # extract host/port
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
  while ! nc -z "$PGHOST" "$PGPORT"; do
    sleep 0.1
  done
  echo "Postgres is up"
fi

# 2) Apply migrations & collectstatic
echo "→ apply migrations"
python manage.py migrate --no-input

echo "→ collect static"
python manage.py collectstatic --no-input --clear

# 3) (Optional) seed your table if empty
TABLE_COUNT=$(printf "SELECT COUNT(*) FROM rna_exonconservation;\n" | python manage.py dbshell | tr -dc '0-9')
if [ "$TABLE_COUNT" -eq 0 ]; then
  echo "→ import_data.py (first-time load)"
  python data/import_data.py
else
  echo "→ data already present; skipping import"
fi

# 4) Launch Gunicorn on the Render-provided port
exec gunicorn exon.wsgi:application \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers 3