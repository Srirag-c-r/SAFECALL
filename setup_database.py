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
    
    # Run collectstatic to gather all static files
    try:
        print("Running collectstatic...")
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--no-input"], check=True)
        print("Collectstatic completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running collectstatic: {e}")
        print("Trying to copy files manually as a fallback...")
    
    # Source and destination directories
    static_root = os.path.join(BASE_DIR, "staticfiles")
    static_source = os.path.join(BASE_DIR, "static")
    
    # Always verify important directories exist in staticfiles
    important_dirs = ["LOGOS", "css", "js", "images"]
    for dir_name in important_dirs:
        os.makedirs(os.path.join(static_root, dir_name), exist_ok=True)
    
    # List of critical files that must be copied correctly
    critical_files = [
        {"src": os.path.join(static_source, "LOGOS", "papereffect.mp4"), 
         "dst": os.path.join(static_root, "LOGOS", "papereffect.mp4")},
        {"src": os.path.join(static_source, "LOGOS", "gpttlogo.png"), 
         "dst": os.path.join(static_root, "LOGOS", "gpttlogo.png")},
        {"src": os.path.join(static_source, "LOGOS", "CREATOR.jpeg"), 
         "dst": os.path.join(static_root, "LOGOS", "CREATOR.jpeg")},
    ]
    
    # Force-copy all critical files
    for file_info in critical_files:
        src_path = file_info["src"]
        dst_path = file_info["dst"]
        
        if os.path.exists(src_path):
            try:
                print(f"Copying critical file: {os.path.basename(src_path)}")
                # Use binary mode for all files to ensure integrity
                with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                    dst.write(src.read())
                
                # Verify file size
                src_size = os.path.getsize(src_path)
                dst_size = os.path.getsize(dst_path)
                if src_size != dst_size:
                    print(f"WARNING: File size mismatch for {os.path.basename(src_path)}: {src_size} vs {dst_size}")
                else:
                    print(f"Successfully copied and verified: {os.path.basename(src_path)} ({src_size} bytes)")
            except Exception as e:
                print(f"ERROR copying {os.path.basename(src_path)}: {e}")
        else:
            print(f"WARNING: Critical file not found: {src_path}")
    
    # Copy all files from LOGOS directory
    logos_src = os.path.join(static_source, "LOGOS")
    logos_dst = os.path.join(static_root, "LOGOS")
    
    if os.path.exists(logos_src):
        print(f"Copying all logo files from {logos_src} to {logos_dst}...")
        try:
            for filename in os.listdir(logos_src):
                src_file = os.path.join(logos_src, filename)
                dst_file = os.path.join(logos_dst, filename)
                
                # Skip directories
                if os.path.isdir(src_file):
                    continue
                    
                # Copy with binary mode
                try:
                    with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
                        dst.write(src.read())
                    print(f"Copied: {filename}")
                except Exception as e:
                    print(f"Error copying {filename}: {e}")
        except Exception as e:
            print(f"Error accessing logos directory: {e}")
    
    # Print summary of staticfiles directory
    print("\nStatic files setup summary:")
    if os.path.exists(static_root):
        count = sum(1 for _ in os.walk(static_root))
        print(f"Total directories in staticfiles: {count}")
        
        file_count = sum(len(files) for _, _, files in os.walk(static_root))
        print(f"Total files in staticfiles: {file_count}")
        
        # Check if critical directories have files
        for dir_name in important_dirs:
            dir_path = os.path.join(static_root, dir_name)
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                print(f"Files in {dir_name}: {len(files)}")
                if dir_name == "LOGOS":
                    print(f"LOGOS files: {files}")
    else:
        print("WARNING: staticfiles directory doesn't exist!")

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