"""
Middleware to add cache control headers to prevent browser back button from displaying
logged in pages after logout
"""

import sys
import traceback
import logging
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

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

class ExceptionLoggingMiddleware:
    """
    Middleware to catch, log, and optionally display all exceptions.
    This helps diagnose 500 errors in production.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Get full traceback
        exc_info = sys.exc_info()
        error_text = "".join(traceback.format_exception(*exc_info))
        
        # Log the full error with request details
        error_msg = f"EXCEPTION IN REQUEST: {request.path}\n{error_text}"
        logger.error(error_msg)
        print(error_msg)  # For console/log output
        
        # In debug mode, display the error directly
        if settings.DEBUG:
            return HttpResponse(
                f"<h1>Server Error Details</h1>"
                f"<h2>Path: {request.path}</h2>"
                f"<pre>{error_text}</pre>",
                content_type="text/html",
                status=500
            )
            
        return None  # Let Django handle it normally
