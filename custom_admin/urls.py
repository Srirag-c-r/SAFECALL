from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.AdminLogoutView.as_view(), name='logout'),
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('download-report/', views.DownloadReportView.as_view(), name='download_report'),
    path('add-police-station/', views.AddPoliceStationView.as_view(), name='add_police_station'),
    path('edit-user/', views.EditUserView.as_view(), name='edit_user'),
    path('complaints/', views.ComplaintListView.as_view(), name='complaints'),
    path('complaints/<int:complaint_id>/', views.ComplaintDetailView.as_view(), name='complaint_detail'),
    path('donations/', views.DonationHistoryView.as_view(), name='donation_history'),
    path('donation-details/<int:donation_id>/', views.DonationDetailView.as_view(), name='donation_details'),
]
