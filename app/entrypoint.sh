#!/bin/sh
python manage.py migrate
python data/import_data.py
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# python manage.py flush --no-input
# python manage.py migrate

exec "$@"