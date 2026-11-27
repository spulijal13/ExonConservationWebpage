#!/bin/sh
set -eu
cd /app
python manage.py migrate --noinput
python manage.py import_exons --assembly hg19
python manage.py import_exons --assembly hg38
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
