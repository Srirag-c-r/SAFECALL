"""
URL configuration for safecall project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Includes the core app URLs
    path('custom-admin/', include('custom_admin.urls')),  # Include custom admin URLs
    path('create-donation-order/', views.create_donation_order, name='create_donation_order'),
    path('verify-donation/', views.verify_donation, name='verify_donation'),
    path('donate/', views.donate, name='donate'),
]

# Serve static files during development and in production
from django.views.static import serve
from core.static_handler import serve_static_file

if settings.DEBUG:
    # Use Django's built-in static file serving for development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # For production - use our custom static file handler for better control
    urlpatterns += [
        # Serve static files with our custom handler
        path('static/<path:path>', serve_static_file, name='serve_static'),
        # Serve media files with Django's built-in handler
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# Remove duplicate media serving
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

