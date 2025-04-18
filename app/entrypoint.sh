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
    echo "Creating rna_exonconservation table if not exists..."
    python app/manage.py dbshell <<EOF
CREATE TABLE IF NOT EXISTS rna_exonconservation (
    id BIGSERIAL PRIMARY KEY,
    exon_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    chrm VARCHAR(50) NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    info VARCHAR(255) NOT NULL,
    strand VARCHAR(255) NOT NULL,
    length INTEGER NOT NULL,
    exon_number VARCHAR(255) NOT NULL,
    total_exon INTEGER NOT NULL,
    exon_type VARCHAR(255) NOT NULL,
    previous_intron VARCHAR(255) NOT NULL,
    next_intron VARCHAR(255) NOT NULL,
    ss_score3 DOUBLE PRECISION NOT NULL,
    ss_score5 DOUBLE PRECISION NOT NULL,
    phastcons_100 VARCHAR(255) NOT NULL,
    ultra_in VARCHAR(255) NOT NULL,
    prime3 VARCHAR(255) NOT NULL,
    prime5 VARCHAR(255) NOT NULL,
    cassette VARCHAR(255) NOT NULL,
    const VARCHAR(255) NOT NULL,
    similarity_score VARCHAR(255) NOT NULL,
    phylo_p DOUBLE PRECISION NOT NULL,
    gene_phylo_p VARCHAR(255) NOT NULL,
    genes_ultra VARCHAR(255) NOT NULL
);
EOF
fi

echo "Collecting static files..."
python app/manage.py collectstatic --noinput

echo "Starting Django server..."
exec python app/manage.py runserver 0.0.0.0:8000