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
from pathlib import Path

MAX_RETRIES = 5
RETRY_INTERVAL = 5  # seconds

def setup_database():
    """Setup the database with initial migrations"""
    print("Running database migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        # Continue anyway, since other setup steps are important

def setup_static_files():
    """Prepare static files for production"""
    print("Setting up static files...")
    
    # Get the base directory
    BASE_DIR = Path(__file__).resolve().parent
    
    # Create necessary static directories
    static_dirs = [
        os.path.join(BASE_DIR, "static"),
        os.path.join(BASE_DIR, "static", "css"),
        os.path.join(BASE_DIR, "static", "js"),
        os.path.join(BASE_DIR, "static", "images"),
        os.path.join(BASE_DIR, "static", "LOGOS"),
        os.path.join(BASE_DIR, "staticfiles"),
    ]
    
    for directory in static_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Run collectstatic again to be sure
    try:
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--no-input"], check=True)
        print("Collectstatic completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running collectstatic: {e}")
    
    # Debug information
    static_root = os.path.join(BASE_DIR, "staticfiles")
    print(f"STATIC_ROOT directory: {static_root}")
    if os.path.exists(static_root):
        files = os.listdir(static_root)
        print(f"Files in STATIC_ROOT: {files[:10]}")
        print(f"Total files in STATIC_ROOT: {len(files)}")
        
        # Check for specific important files
        logo_path = os.path.join(static_root, "LOGOS")
        if os.path.exists(logo_path):
            logo_files = os.listdir(logo_path)
            print(f"Files in LOGOS directory: {logo_files}")
        else:
            print("LOGOS directory not found in staticfiles!")
            
            # Create it and copy files from static
            os.makedirs(logo_path, exist_ok=True)
            source_logos = os.path.join(BASE_DIR, "static", "LOGOS")
            if os.path.exists(source_logos):
                for file in os.listdir(source_logos):
                    src_file = os.path.join(source_logos, file)
                    dst_file = os.path.join(logo_path, file)
                    shutil.copy2(src_file, dst_file)
                    print(f"Copied {file} to {logo_path}")
    else:
        print("STATIC_ROOT directory does not exist!")

def wait_for_database():
    """Wait for database to be available"""
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            conn = connections['default']
            conn.cursor()
            print("Database connection established.")
            return True
        except OperationalError:
            retry_count += 1
            if retry_count < MAX_RETRIES:
                print(f"Database connection attempt {retry_count} failed. Retrying in {RETRY_INTERVAL} seconds...")
                time.sleep(RETRY_INTERVAL)
            else:
                print(f"Could not connect to database after {MAX_RETRIES} attempts.")
                return False

def main():
    """Main setup function."""
    # Set up Django environment
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safecall.settings")
    
    # First setup static files
    setup_static_files()
    
    # Wait for database
    print("Checking database connection...")
    db_ready = wait_for_database()
    
    if db_ready:
        # Run migrations
        setup_database()
        print("Database setup complete.")
    else:
        print("WARNING: Database not available, skipping migrations.")
        
    print("Setup completed.")
    return db_ready

if __name__ == "__main__":
    # Add the project path to sys.path
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_path)
    
    # Set up Django environment
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safecall.settings")
    
    main() 