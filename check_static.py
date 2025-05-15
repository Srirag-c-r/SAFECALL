#!/usr/bin/env python
"""
Static files checker utility for SafeCall project.
This script helps diagnose issues with static files by checking
their presence and configuration.
"""

import os
import sys
import shutil
from pathlib import Path

# Add the project path to sys.path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "safecall.settings")

import django
django.setup()

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command

def print_separator():
    print("\n" + "=" * 70 + "\n")

def check_static_config():
    """Check Django static files configuration"""
    print("CHECKING DJANGO STATIC FILES CONFIGURATION")
    print_separator()
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    print(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    middleware_names = [m.split('.')[-1] for m in settings.MIDDLEWARE]
    print(f"WhiteNoise in middleware: {'WhiteNoiseMiddleware' in middleware_names}")
    
    print_separator()

def check_static_dirs():
    """Check if static directories exist and contain files"""
    print("CHECKING STATIC DIRECTORIES")
    print_separator()
    
    # Check STATICFILES_DIRS
    for directory in settings.STATICFILES_DIRS:
        if os.path.exists(directory):
            file_count = sum(1 for _ in os.listdir(directory) if os.path.isfile(os.path.join(directory, _)))
            print(f"Directory exists: {directory} - {file_count} files")
            
            # Check LOGOS directory
            logos_dir = os.path.join(directory, 'LOGOS')
            if os.path.exists(logos_dir):
                logo_files = [f for f in os.listdir(logos_dir) if os.path.isfile(os.path.join(logos_dir, f))]
                print(f"  LOGOS directory: {logos_dir}")
                print(f"  Files in LOGOS: {logo_files}")
            else:
                print(f"  WARNING: LOGOS directory not found in {directory}")
        else:
            print(f"WARNING: Directory does not exist: {directory}")
    
    # Check STATIC_ROOT
    if settings.STATIC_ROOT:
        if os.path.exists(settings.STATIC_ROOT):
            file_count = sum(len(files) for _, _, files in os.walk(settings.STATIC_ROOT))
            print(f"\nSTATIC_ROOT: {settings.STATIC_ROOT} - {file_count} total files")
            
            # Check important subdirectories in STATIC_ROOT
            for subdir in ['LOGOS', 'css', 'js', 'images']:
                check_dir = os.path.join(settings.STATIC_ROOT, subdir)
                if os.path.exists(check_dir):
                    subdir_files = [f for f in os.listdir(check_dir) if os.path.isfile(os.path.join(check_dir, f))]
                    print(f"  {subdir} directory: {len(subdir_files)} files")
                    if subdir == 'LOGOS':
                        print(f"  Files in LOGOS: {subdir_files}")
                else:
                    print(f"  WARNING: {subdir} directory not found in STATIC_ROOT")
        else:
            print(f"\nWARNING: STATIC_ROOT does not exist: {settings.STATIC_ROOT}")
    else:
        print("\nWARNING: STATIC_ROOT is not defined")
    
    print_separator()

def check_critical_files():
    """Check if critical static files exist"""
    print("CHECKING CRITICAL STATIC FILES")
    print_separator()
    
    critical_files = [
        'LOGOS/papereffect.mp4',
        'LOGOS/gpttlogo.png',
        'LOGOS/CREATOR.jpeg',
    ]
    
    for file_path in critical_files:
        # Check using Django's finders
        found_path = finders.find(file_path)
        if found_path:
            file_size = os.path.getsize(found_path)
            print(f"File found: {file_path} - {file_size} bytes at {found_path}")
        else:
            print(f"WARNING: File not found by finders: {file_path}")
            
            # Check manually in STATICFILES_DIRS
            for directory in settings.STATICFILES_DIRS:
                full_path = os.path.join(directory, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    print(f"  Found in STATICFILES_DIRS: {full_path} - {file_size} bytes")
            
            # Check manually in STATIC_ROOT
            if settings.STATIC_ROOT:
                full_path = os.path.join(settings.STATIC_ROOT, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    print(f"  Found in STATIC_ROOT: {full_path} - {file_size} bytes")
    
    print_separator()

def fix_missing_files():
    """Fix missing critical files by copying them"""
    print("FIXING MISSING STATIC FILES")
    print_separator()
    
    # Define critical files with source and destination
    BASE_DIR = Path(__file__).resolve().parent
    
    critical_files = [
        {
            'src': os.path.join(BASE_DIR, 'static', 'LOGOS', 'papereffect.mp4'),
            'dst': os.path.join(settings.STATIC_ROOT, 'LOGOS', 'papereffect.mp4'),
            'name': 'Video background'
        },
        {
            'src': os.path.join(BASE_DIR, 'static', 'LOGOS', 'gpttlogo.png'),
            'dst': os.path.join(settings.STATIC_ROOT, 'LOGOS', 'gpttlogo.png'),
            'name': 'Logo'
        },
        {
            'src': os.path.join(BASE_DIR, 'static', 'LOGOS', 'CREATOR.jpeg'),
            'dst': os.path.join(settings.STATIC_ROOT, 'LOGOS', 'CREATOR.jpeg'),
            'name': 'Creator image'
        },
    ]
    
    # Make sure LOGOS directory exists in STATIC_ROOT
    os.makedirs(os.path.join(settings.STATIC_ROOT, 'LOGOS'), exist_ok=True)
    
    # Copy each critical file
    for file_info in critical_files:
        src = file_info['src']
        dst = file_info['dst']
        name = file_info['name']
        
        if os.path.exists(src):
            print(f"Copying {name} from {src} to {dst}")
            try:
                # Use binary mode to copy file
                with open(src, 'rb') as src_file, open(dst, 'wb') as dst_file:
                    dst_file.write(src_file.read())
                
                # Verify file size
                src_size = os.path.getsize(src)
                dst_size = os.path.getsize(dst)
                if src_size == dst_size:
                    print(f"  Success: {src_size} bytes copied correctly.")
                else:
                    print(f"  WARNING: File sizes don't match. Source: {src_size}, Dest: {dst_size}")
            except Exception as e:
                print(f"  ERROR: Failed to copy {name}: {e}")
        else:
            print(f"WARNING: Source file {name} not found at {src}")
    
    print_separator()

def run_collectstatic():
    """Run Django's collectstatic command"""
    print("RUNNING COLLECTSTATIC")
    print_separator()
    
    try:
        call_command('collectstatic', interactive=False, clear=True, verbosity=1)
        print("Collectstatic completed successfully.")
    except Exception as e:
        print(f"ERROR: Collectstatic failed: {e}")
    
    print_separator()

def main():
    """Main function to run all checks and fixes"""
    print("\nSTATIC FILES DIAGNOSTIC TOOL")
    print("===========================\n")
    
    # Check Django configuration
    check_static_config()
    
    # Check if static directories exist
    check_static_dirs()
    
    # Check if critical files exist
    check_critical_files()
    
    # Ask user if they want to fix issues
    fix_choice = input("Do you want to fix missing files? (y/n): ")
    if fix_choice.lower() == 'y':
        fix_missing_files()
    
    # Ask user if they want to run collectstatic
    collect_choice = input("Do you want to run collectstatic? (y/n): ")
    if collect_choice.lower() == 'y':
        run_collectstatic()
    
    print("\nDiagnostic completed. Check the output above for any issues.")

if __name__ == "__main__":
    main() 