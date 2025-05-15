#!/usr/bin/env python
"""
Database setup script that runs migrations after ensuring
the database connection is properly established.
"""
import os
import sys
import time
import subprocess
import django
import shutil
from django.db import connections
from django.db.utils import OperationalError

MAX_RETRIES = 5
RETRY_INTERVAL = 5  # seconds

def ensure_static_files():
    """Ensure static files are correctly set up."""
    project_path = os.path.dirname(os.path.abspath(__file__))
    
    # Create static directories if they don't exist
    static_dir = os.path.join(project_path, "static")
    staticfiles_dir = os.path.join(project_path, "staticfiles")
    
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(staticfiles_dir, exist_ok=True)
    
    # Create subdirectories 
    for subdir in ['css', 'js', 'images', 'LOGOS']:
        os.makedirs(os.path.join(static_dir, subdir), exist_ok=True)
    
    # Ensure LOGOS directory exists in staticfiles
    logos_dir = os.path.join(staticfiles_dir, "LOGOS")
    if not os.path.exists(logos_dir):
        os.makedirs(logos_dir, exist_ok=True)
    
    # Copy logo files to make sure they're in the staticfiles directory
    source_logos_dir = os.path.join(static_dir, "LOGOS")
    if os.path.exists(source_logos_dir):
        for file in os.listdir(source_logos_dir):
            source_path = os.path.join(source_logos_dir, file)
            target_path = os.path.join(logos_dir, file)
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                print(f"Copied logo file: {file} to staticfiles/LOGOS")

def main():
    """Run Django migrations after ensuring database is connected."""
    # First ensure static files are set up
    ensure_static_files()
    
    print("Checking database connection...")
    
    # Wait for database to be ready
    for i in range(MAX_RETRIES):
        try:
            # Try to connect to the database
            django.setup()
            connections['default'].cursor()
            print("Database connection successful!")
            break
        except OperationalError:
            print(f"Database connection attempt {i+1}/{MAX_RETRIES} failed. Retrying in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)
        except Exception as e:
            print(f"Unexpected error connecting to database: {e}")
            # If there's an unexpected error, try to continue anyway
            break
    
    # Run migrations
    print("Running migrations...")
    try:
        result = subprocess.run(
            ["python", "manage.py", "migrate", "--noinput"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Migration output:")
        print(result.stdout)
        if result.stderr:
            print("Migration errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with error code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        return False
    
    print("Database setup complete.")
    return True

if __name__ == "__main__":
    # Add the project path to sys.path
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_path)
    
    # Set up Django environment
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safecall.settings")
    
    success = main()
    sys.exit(0 if success else 1) 