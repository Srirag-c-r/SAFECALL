from django.urls import path
from . import views

urlpatterns = [
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
    
    # Logout
    path('logout/', views.user_logout, name='user_logout'),
    
    # Police station logout
    path('police_station/logout/', views.police_station_logout, name='police_logout'),  # Add this line
]
