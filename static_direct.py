"""
Direct static file handler for Render deployment
This script ensures static files are properly served in production
"""
import os
import shutil
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

def copy_static_files():
    """
    Copy static files to a direct access directory
    """
    print("Setting up direct static file access...")
    
    # Create direct static directory
    direct_static_dir = os.path.join(BASE_DIR, 'direct_static')
    os.makedirs(direct_static_dir, exist_ok=True)
    
    # Create subdirectories
    for subdir in ['LOGOS', 'css', 'js', 'images']:
        os.makedirs(os.path.join(direct_static_dir, subdir), exist_ok=True)
    
    # Copy files from static directory
    static_dir = os.path.join(BASE_DIR.parent, 'static')
    
    if os.path.exists(static_dir):
        # Copy LOGOS
        logos_src = os.path.join(static_dir, 'LOGOS')
        logos_dest = os.path.join(direct_static_dir, 'LOGOS')
        if os.path.exists(logos_src):
            for item in os.listdir(logos_src):
                src_path = os.path.join(logos_src, item)
                dest_path = os.path.join(logos_dest, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {item} to direct static LOGOS")
        
        # Copy CSS
        css_src = os.path.join(static_dir, 'css')
        css_dest = os.path.join(direct_static_dir, 'css')
        if os.path.exists(css_src):
            for item in os.listdir(css_src):
                src_path = os.path.join(css_src, item)
                dest_path = os.path.join(css_dest, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {item} to direct static CSS")
        
        # Copy JS
        js_src = os.path.join(static_dir, 'js')
        js_dest = os.path.join(direct_static_dir, 'js')
        if os.path.exists(js_src):
            for item in os.listdir(js_src):
                src_path = os.path.join(js_src, item)
                dest_path = os.path.join(js_dest, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {item} to direct static JS")
        
        # Copy images
        images_src = os.path.join(static_dir, 'images')
        images_dest = os.path.join(direct_static_dir, 'images')
        if os.path.exists(images_src):
            for item in os.listdir(images_src):
                src_path = os.path.join(images_src, item)
                dest_path = os.path.join(images_dest, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {item} to direct static images")
    
    print("Direct static file setup complete!")

if __name__ == "__main__":
    copy_static_files()
