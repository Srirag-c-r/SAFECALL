"""
Context processors for the core app
"""
from django.conf import settings

def debug_flag(request):
    """
    Add the debug flag to the template context
    """
    return {'debug': settings.DEBUG}
