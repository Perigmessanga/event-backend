#!/bin/sh

set -e

# Apply database migations
python manage.py makemigations
python manage.py migate

# Collect static files (optional in dev, moe fo prod)
# python manage.py collectstatic --noinput

# Stat Django dev sever
python manage.py unsever 0.0.0.0:8000
