"""
Middleware to add cache control headers to prevent browser back button from displaying
logged in pages after logout, and to ensure static files are properly served
"""
import os
from django.conf import settings

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if we're on a protected page that requires authentication
        protected_urls = [
            '/user/dashboard/',
            '/police_station/dashboard/',
            '/user/profile/',
            '/user/complaints/',
            '/police_station/analytics/',
            '/police_station/complaints/'
        ]
        
        # Add cache control headers for these protected pages
        if any(request.path.startswith(url) for url in protected_urls):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class StaticFilesHeadersMiddleware:
    """
    Middleware to add proper headers for static files to ensure they're properly served
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if the request is for a static file
        if request.path.startswith(settings.STATIC_URL):
            # Get the file extension
            _, ext = os.path.splitext(request.path)
            ext = ext.lower()[1:] if ext else ''
            
            # Set appropriate headers based on file type
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
                response['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
            elif ext in ['mp4', 'webm', 'mov']:
                response['Cache-Control'] = 'public, max-age=31536000'
                # Ensure proper content type for videos
                if ext == 'mp4':
                    response['Content-Type'] = 'video/mp4'
            elif ext in ['css', 'js']:
                response['Cache-Control'] = 'public, max-age=31536000'
            
            # Ensure CORS headers for static files
            response['Access-Control-Allow-Origin'] = '*'
        
        return response
