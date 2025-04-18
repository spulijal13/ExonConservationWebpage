#!/bin/sh

set -e  # Exit immediately on error

cd /app || exit 1

if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for Postgres at $SQL_HOST:$SQL_PORT..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
        sleep 0.5
    done
    echo "PostgreSQL started"
fi

echo "Running makemigrations and migrate..."
python app/manage.py makemigrations --noinput
python app/manage.py migrate --noinput

# Check if the table exists (without causing the script to fail if it doesn't)
TABLE_EXISTS=$(python app/manage.py dbshell <<EOF
SELECT to_regclass('public.rna_exonconservation');
EOF
)

TABLE_EXISTS=$(echo "$TABLE_EXISTS" | grep -o 'rna_exonconservation')

if [ "$TABLE_EXISTS" = "rna_exonconservation" ]; then
    echo "Table exists. Checking row count..."

    TABLE_COUNT=$(python app/manage.py dbshell <<EOF
SELECT COUNT(*) FROM rna_exonconservation;
EOF
)
    TABLE_COUNT=$(echo "$TABLE_COUNT" | tr -cd '[:digit:]')

    if [ "$TABLE_COUNT" -eq 0 ]; then
        echo "Table is empty. Importing data..."
        python /app/data/import_data.py
    else
        echo "Table has data. Skipping import."
    fi
else
    echo "Table rna_exonconservation does not exist."
fi

echo "Collecting static files..."
python app/manage.py collectstatic --noinput

echo "Starting Django server..."
exec python app/manage.py runserver 0.0.0.0:8000