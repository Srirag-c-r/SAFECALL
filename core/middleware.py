"""
Middleware to add cache control headers to prevent browser back button from displaying
logged in pages after logout
"""

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
