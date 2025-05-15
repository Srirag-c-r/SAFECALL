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
from django.db import connections
from django.db.utils import OperationalError

MAX_RETRIES = 5
RETRY_INTERVAL = 5  # seconds

def main():
    """Run Django migrations after ensuring database is connected."""
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