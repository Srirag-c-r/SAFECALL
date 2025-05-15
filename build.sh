#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies using the right requirements file
pip install -r requirements-render.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input 