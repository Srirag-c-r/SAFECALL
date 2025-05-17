"""
Management command to prepare static files for deployment
"""
import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Prepares static files for deployment by creating direct access copies'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting static files preparation for deployment...'))
        
        # Get base directory
        base_dir = Path(settings.BASE_DIR)
        
        # Create direct static directory
        direct_static_dir = os.path.join(base_dir, 'direct_static')
        os.makedirs(direct_static_dir, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['LOGOS', 'css', 'js', 'images']:
            os.makedirs(os.path.join(direct_static_dir, subdir), exist_ok=True)
        
        # Copy files from static directory
        static_dir = os.path.join(base_dir.parent, 'static')
        
        if os.path.exists(static_dir):
            # Copy LOGOS
            self._copy_directory(
                os.path.join(static_dir, 'LOGOS'),
                os.path.join(direct_static_dir, 'LOGOS'),
                'LOGOS'
            )
            
            # Copy CSS
            self._copy_directory(
                os.path.join(static_dir, 'css'),
                os.path.join(direct_static_dir, 'css'),
                'CSS'
            )
            
            # Copy JS
            self._copy_directory(
                os.path.join(static_dir, 'js'),
                os.path.join(direct_static_dir, 'js'),
                'JS'
            )
            
            # Copy images
            self._copy_directory(
                os.path.join(static_dir, 'images'),
                os.path.join(direct_static_dir, 'images'),
                'images'
            )
        
        # Create symbolic links in staticfiles directory
        staticfiles_dir = os.path.join(base_dir.parent, 'staticfiles')
        if os.path.exists(staticfiles_dir):
            direct_dir = os.path.join(staticfiles_dir, 'direct')
            os.makedirs(direct_dir, exist_ok=True)
            
            # Create symlinks or copy files
            self._create_link_or_copy(
                os.path.join(direct_static_dir, 'LOGOS'),
                os.path.join(direct_dir, 'LOGOS'),
                'LOGOS'
            )
            
            self._create_link_or_copy(
                os.path.join(direct_static_dir, 'css'),
                os.path.join(direct_dir, 'css'),
                'CSS'
            )
            
            self._create_link_or_copy(
                os.path.join(direct_static_dir, 'js'),
                os.path.join(direct_dir, 'js'),
                'JS'
            )
            
            self._create_link_or_copy(
                os.path.join(direct_static_dir, 'images'),
                os.path.join(direct_dir, 'images'),
                'images'
            )
        
        self.stdout.write(self.style.SUCCESS('Static files preparation complete!'))
    
    def _copy_directory(self, src_dir, dest_dir, dir_name):
        """Copy files from source directory to destination directory"""
        if os.path.exists(src_dir):
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dest_path = os.path.join(dest_dir, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    self.stdout.write(f"Copied {item} to direct static {dir_name}")
        else:
            self.stdout.write(self.style.WARNING(f"Source directory {src_dir} does not exist"))
    
    def _create_link_or_copy(self, src_dir, dest_dir, dir_name):
        """Create symbolic link or copy directory if linking fails"""
        try:
            # Try to create a symbolic link
            if os.path.exists(dest_dir):
                if os.path.islink(dest_dir):
                    os.unlink(dest_dir)
                else:
                    shutil.rmtree(dest_dir)
            
            os.symlink(src_dir, dest_dir, target_is_directory=True)
            self.stdout.write(f"Created symbolic link for {dir_name}")
        except (OSError, NotImplementedError):
            # If symbolic linking fails, copy the files instead
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            
            shutil.copytree(src_dir, dest_dir)
            self.stdout.write(f"Copied directory for {dir_name} (symlink failed)")
