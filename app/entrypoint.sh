#!/bin/sh
# Prepare local data, then start the development server.
set -eu
cd /app
sh ./prepare.sh
exec python manage.py runserver 0.0.0.0:8000
