#!/bin/sh
# Run from the app directory: update schema, import both CSVs, collect web assets.
# Stop on the first error so the server cannot start with incomplete preparation.
set -eu
python manage.py migrate --noinput
python manage.py import_exons --assembly hg19
python manage.py import_exons --assembly hg38
python manage.py collectstatic --noinput
