#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting enhanced build process for deployment..."

# Install dependencies using the right requirements file
echo "Installing dependencies..."
pip install -r requirements-render.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Set up direct static file access using our custom management command
echo "Setting up direct static file access..."
python manage.py prepare_static_files

echo "Build process completed successfully!"