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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from core import views
from django.http import HttpResponse
from core.views import serve_media_file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Includes the core app URLs
    path('custom-admin/', include('custom_admin.urls')),  # Include custom admin URLs
    path('create-donation-order/', views.create_donation_order, name='create_donation_order'),
    path('verify-donation/', views.verify_donation, name='verify_donation'),
    path('donate/', views.donate, name='donate'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'LOGOS/gpttlogo.png')),
    
    # Debug route to check if server is responding
    path('server-status/', lambda request: HttpResponse("Server is running", content_type="text/plain")),
]

# Add media file serving fallback for production
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_media_file),
]

# Add static file handling in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Remove duplicate media serving
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

