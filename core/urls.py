# Add these to your urls.py file

# Existing imports
from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Your existing URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # Registration
    path('register/', views.register, name='register'),
    path('register/public/', views.public_user_registration, name='public_user_registration'),
    path('register/police/', views.police_station_registration, name='police_station_registration'),

    # OTP verification
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # Login
    path('login/', views.login_view, name='login'),
    path('login/user/', views.user_login, name='user_login'),
    path('login/police_station/', views.police_station_login, name='police_station_login'),

    # Dashboards
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('police_station/dashboard/', views.police_station_dashboard, name='police_station_dashboard'),
    path('police_station/analytics/', views.police_station_analytics, name='police_station_analytics'),

    # Complaints
    path('user/add-complaint/', views.add_complaint, name='add_complaint'),
    path('get-locations/', views.get_locations, name='get_locations'),
    path('user/view-complaints/', views.view_complaints, name='view_complaints'),
    
    # New URLs for police station complaint management
    path('police_station/view-complaints/', views.police_view_complaints, name='police_view_complaints'),
    path('police_station/update-complaint/<int:complaint_id>/<str:action>/', 
         views.update_complaint_status, name='update_complaint_status'),

    # Logout
    path('logout/', views.user_logout, name='user_logout'),
    path('police_station/logout/', views.police_station_logout, name='police_logout'),
    # Add these URLs to your urlpatterns list
    path('user/view-fir/<int:complaint_id>/', views.view_fir, name='view_fir'),
    path('user/download-fir/<int:complaint_id>/', views.download_fir, name='download_fir'),

    path('police/view-complaints/', views.police_view_complaints, name='police_view_complaints'),
    path('police/manage-fir/', views.manage_fir, name='manage_fir'),
    path('police/create-fir/<int:complaint_id>/', views.create_fir, name='create_fir'),
    path('police/resolve-complaint/<int:complaint_id>/', views.resolve_complaint, name='resolve_complaint'),
    path('fir/<int:complaint_id>/add-witness/', views.add_witness_to_fir, name='add_witness_to_fir'),
    path('fir/<int:complaint_id>/add-evidence/', views.add_evidence_to_fir, name='add_evidence_to_fir'),
    path('fir/<int:complaint_id>/add-description/', views.add_description_to_fir, name='add_description_to_fir'),
    path('fir/<int:complaint_id>/case-file/', views.view_case_file, name='view_case_file'),
    
    # Password Reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),

    # Contact page
    path('contact/', views.contact, name='contact'),
    
    # Profile Update
    path('user/update-profile/', views.update_profile, name='update_profile'),

    # Donation URLs
    path('donate/', views.donate, name='donate'),
    path('create-donation-order/', views.create_donation_order, name='create_donation_order'),
    path('verify-donation/', views.verify_donation, name='verify_donation'),
    path('custom-admin/donation-details/<int:donation_id>/', views.donation_details, name='donation_details'),

    path('get-complete-report/<int:complaint_id>/', views.get_complete_report, name='get_complete_report'),
    
    # Debug URL - only available with special key in production
    path('debug-info/', views.debug_info, name='debug_info'),

    # Add this new URL for debugging
    path('debug-static/', views.debug_static_files, name='debug_static_files'),

    # Add URL for checking video files
    path('check-video/<str:filename>/', views.check_video_file, name='check_video_file'),

    # Direct video file serving as fallback
    path('serve-video/<str:filename>/', views.serve_video_file, name='serve_video_file'),

    # File check utility
    path('file-check/', views.file_check, name='file_check'),
    
    # API configuration check
    path('api-config-check/', views.api_config_check, name='api_config_check'),

    # Add URL for error check
    path('error-check/', views.error_check, name='error_check'),
    path('diagnostics/', TemplateView.as_view(template_name='core/error_check.html'), name='diagnostics'),
    
    # Add privacy policy URL
    path('privacy-policy/', TemplateView.as_view(template_name='core/privacy_policy.html'), name='privacy_policy'),
]