#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear superusuario solo si no existe (no falla el deploy si ya está)
python manage.py createsuperuser --noinput || true