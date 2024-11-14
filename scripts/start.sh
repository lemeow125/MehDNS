#!/bin/bash

cd backend/
python manage.py graph_models -o ../documentation/erd/app_models.png
python manage.py spectacular --color --file schema.yml
python manage.py migrate
python manage.py push_records
if [ ! -d "static" ]; then
    echo "Generating static files"
    python manage.py collectstatic --noinput
fi
if [ "$BACKEND_DEBUG" = 'True' ]; then   
    python manage.py runserver "0.0.0.0:8000"
else
    gunicorn --workers 8 --bind 0.0.0.0:8000 config.wsgi:application
fi
