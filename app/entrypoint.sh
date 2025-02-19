#!/bin/sh

cd /app || exit

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "starting django server"
exec python manage.py runserver 0.0.0.0:8000

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

TABLE_COUNT=$(python /app/manage.py dbshell <<EOF
SELECT COUNT(*) FROM rna_exonconservation;
EOF
)

# Remove whitespace from TABLE_COUNT
TABLE_COUNT=$(echo "$TABLE_COUNT" | tr -d '[:space:]')

# ✅ If TABLE_COUNT is 0 (empty table), run `import_data.py`
if [[ "$TABLE_COUNT" -eq "0" ]]; then
    echo "rna_exonconservation is empty. Running import_data.py..."
    python /app/data/import_data.py
else
    echo "rna_exonconservation already has data. Skipping import_data.py."
fi

# python manage.py flush --no-input
# python manage.py migrate

exec "$@"