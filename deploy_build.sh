#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Starting deployment build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-render.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create a special static files directory for deployment
echo "Setting up static files for deployment..."

# Create a special directory for static files that won't be processed by WhiteNoise
mkdir -p ../deployment_static
mkdir -p ../deployment_static/LOGOS
mkdir -p ../deployment_static/css
mkdir -p ../deployment_static/js
mkdir -p ../deployment_static/images

# Copy static files directly (without processing)
echo "Copying static files directly..."
cp -r ../static/LOGOS/* ../deployment_static/LOGOS/
cp -r ../static/css/* ../deployment_static/css/
cp -r ../static/js/* ../deployment_static/js/
cp -r ../static/images/* ../deployment_static/images/

# Collect static files normally as well (for other static files)
echo "Collecting static files with Django..."
python manage.py collectstatic --no-input

# Create a symlink from the deployment_static to the staticfiles directory
echo "Creating symlinks for direct access..."
cd ../staticfiles
ln -sf ../deployment_static/LOGOS LOGOS_direct
ln -sf ../deployment_static/css css_direct
ln -sf ../deployment_static/js js_direct
ln -sf ../deployment_static/images images_direct

echo "Deployment build completed successfully!"
