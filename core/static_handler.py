"""
Custom static files handler to ensure proper serving of static files in production
"""
import os
import mimetypes
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views.static import serve

def serve_static_file(request, path):
    """
    Custom view to serve static files with proper content types and headers
    """
    # Get the full path to the static file
    full_path = os.path.join(settings.STATIC_ROOT, path)
    
    # Check if the file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        # If not in STATIC_ROOT, try STATICFILES_DIRS
        for static_dir in settings.STATICFILES_DIRS:
            alt_path = os.path.join(static_dir, path)
            if os.path.exists(alt_path) and os.path.isfile(alt_path):
                full_path = alt_path
                break
        else:
            # File not found in any static directory
            return HttpResponse(f"Static file not found: {path}", status=404)
    
    # Get the file extension and determine content type
    _, ext = os.path.splitext(full_path)
    ext = ext.lower()[1:] if ext else ''
    
    # Set appropriate content type for common file types
    content_type = None
    if ext == 'mp4':
        content_type = 'video/mp4'
    elif ext == 'webm':
        content_type = 'video/webm'
    elif ext == 'png':
        content_type = 'image/png'
    elif ext in ['jpg', 'jpeg']:
        content_type = 'image/jpeg'
    elif ext == 'gif':
        content_type = 'image/gif'
    elif ext == 'svg':
        content_type = 'image/svg+xml'
    elif ext == 'css':
        content_type = 'text/css'
    elif ext == 'js':
        content_type = 'application/javascript'
    else:
        # Use mimetypes for other file types
        content_type = mimetypes.guess_type(full_path)[0]
    
    # Create a FileResponse with the appropriate content type
    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    
    # Add cache control headers
    response['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
    response['Access-Control-Allow-Origin'] = '*'  # Allow cross-origin access
    
    return response
