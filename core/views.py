from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from .email_utils import send_html_email, send_donation_invoice
from .models import (PublicUser, PoliceStation, Complaint, FIR, FIREvidence, Witness, 
                   ComplaintLog, PasswordResetToken, Donation, FIRDescription)
import random
import string
from datetime import datetime
import razorpay
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import re
from django.utils import timezone
from newsapi import NewsApiClient
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import user_passes_test
from django.core.serializers import serialize
from django.contrib.auth.hashers import make_password, check_password
import sys
import platform

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def is_police(user):
    """Check if the user is a police station user."""
    return hasattr(user, 'policestation') and user.policestation.approved

def update_profile(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please login first')
        return redirect('user_login')
    
    user = get_object_or_404(PublicUser, id=request.session['user_id'])
    
    if request.method == 'POST':
        # Update basic information
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.phone = request.POST.get('phone')
        user.address = request.POST.get('address')
        user.district = request.POST.get('district')
        user.pincode = request.POST.get('pincode')
        user.gender = request.POST.get('gender')
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            user.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        
        # Handle password change
        password = request.POST.get('password')
        if password:
            # Hash the new password
            user.password = make_password(password)
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            fs = FileSystemStorage(location='media/profile_pictures')
            # Delete old profile picture if it exists
            if user.profile_picture:
                try:
                    old_file_path = user.profile_picture.path
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except:
                    pass
            # Save new profile picture
            filename = fs.save(file.name, file)
            user.profile_picture = f'profile_pictures/{filename}'
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('user_dashboard')
    
    return render(request, 'update_profile.html', {'user': user})

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import re
from django.utils import timezone
from newsapi import NewsApiClient
from datetime import datetime, date, timedelta


# Generate a random OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Register Page View
def register(request):
    return render(request, 'register.html')


# Home Page View
from django.db.models import Count
import json

def home(request):
    # Get statistics
    stats = {
        'total_police_stations': PoliceStation.objects.filter(approved=True).count(),
        'total_cases': Complaint.objects.count(),
        'total_firs': FIR.objects.count(),
        'resolved_cases': Complaint.objects.filter(status='Resolved').count(),
        'total_users': PublicUser.objects.count()
    }

    # Get complaint type distribution
    complaint_types = Complaint.objects.values('complaint_type').annotate(
        count=Count('id')
    ).order_by('-count')[:4]

    # Prepare chart data
    stats['complaint_types_labels'] = json.dumps([ct['complaint_type'] for ct in complaint_types])
    stats['complaint_types_data'] = json.dumps([ct['count'] for ct in complaint_types])

    # Get news from NewsAPI
    try:
        newsapi = NewsApiClient(api_key=settings.NEWSAPI_KEY)
        
        # Get news from the last 7 days
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        # First try to get Indian news
        indian_news = newsapi.get_everything(
            q='crime OR police OR law enforcement',
            from_param=from_date,
            to=to_date,
            language='en',
            sort_by='relevancy',
            sources='the-times-of-india,the-hindu,indian-express,hindustan-times,deccan-herald'
        )
        
        # If we have Indian news articles, use them
        if indian_news['articles']:
            news_articles = indian_news['articles'][:6]
        else:
            # If no Indian news, get international news
            international_news = newsapi.get_everything(
                q='crime OR police OR law enforcement',
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy'
            )
            news_articles = international_news['articles'][:6] if international_news['articles'] else []
            
    except Exception as e:
        print(f"Error fetching news: {str(e)}")  # For debugging
        news_articles = []

    return render(request, 'core/home.html', {
        'stats': stats,
        'news_articles': news_articles,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID  # Add Razorpay key ID to context
    })


# About Page View
def about(request):
    # Get real statistics from database
    stats = {
        'resolved_complaints': Complaint.objects.filter(status='Resolved').count(),
        'total_police_stations': PoliceStation.objects.filter(approved=True).count(),
        'satisfaction_rate': '98%',  # This could be calculated from user feedback in future
        'support_hours': '24/7'
    }
    return render(request, 'core/about.html', {'stats': stats})


# Public User Registration View
def public_user_registration(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        adhaar = request.POST.get('adhaar')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if email already exists
        if PublicUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please use a different email or login.')
            return render(request, 'register.html', {
                'is_public_user': True,
                'form_data': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'email': email,
                    'adhaar': adhaar
                }
            })

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'register.html', {
                'is_public_user': True,
                'form_data': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'email': email,
                    'adhaar': adhaar
                }
            })

        # Hash the password before saving
        hashed_password = make_password(password)

        # Creating and saving the PublicUser instance with hashed password
        user = PublicUser(first_name=first_name, last_name=last_name, phone=phone, email=email, adhaar=adhaar, password=hashed_password)
        user.save()

        # Generate OTP
        otp = generate_otp()

        # Send OTP to the user's email
        # Send email with OTP
        send_html_email(
            subject='OTP Verification for Safe Call',
            template_name='core/emails/otp_email.html',
            context={'otp': otp},
            recipient_list=[email]
        )

        # Store OTP in session for later verification
        request.session['otp'] = otp
        request.session['public_user_id'] = user.id

        messages.success(request, 'You have successfully registered. Please check your email for the OTP verification.')
        return redirect('verify_otp')
    return render(request, 'register.html', {'is_public_user': True})


# OTP Verification for Public User
def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == request.session.get('otp'):
            # OTP is valid, mark the user as verified
            user = PublicUser.objects.get(id=request.session.get('public_user_id'))
            user.is_verified = True
            user.save()

            messages.success(request, 'Your OTP has been verified successfully. You can now login.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html')


# Police Station Registration View
def police_station_registration(request):
    if request.method == 'POST':
        district = request.POST.get('district')
        location = request.POST.get('location')
        pincode = request.POST.get('pincode')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if email already exists
        if PoliceStation.objects.filter(email=email).exists():
            messages.error(request, 'A police station with this email already exists. Please use a different email or login.')
            return render(request, 'register.html', {
                'is_police_station': True,
                'form_data': {
                    'district': district,
                    'location': location,
                    'pincode': pincode,
                    'contact': contact,
                    'email': email
                }
            })

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'register.html', {
                'is_police_station': True,
                'form_data': {
                    'district': district,
                    'location': location,
                    'pincode': pincode,
                    'contact': contact,
                    'email': email
                }
            })

        # Hash the password before saving
        hashed_password = make_password(password)

        # Save the police station record
        police_station = PoliceStation(
            district=district,
            location=location,
            pincode=pincode,
            contact=contact,
            email=email,
            password=hashed_password
        )
        police_station.save()

        messages.success(request, 'Your police station has been registered. It will be approved by the admin soon.')
        return redirect('home')

    return render(request, 'register.html', {'is_police_station': True})


# Login View (General login page)
def login_view(request):
    if request.method == 'POST':
        login_type = request.POST.get('login_as')
        
        # Redirect to respective login page
        if login_type == 'user':
            return redirect('user_login')
        elif login_type == 'police_station':
            return redirect('police_station_login')
        
    return render(request, 'login.html')


# User Login
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = PublicUser.objects.get(email=email)  # Fetch user by email
            if check_password(password, user.password):  # Verify password
                request.session['user_id'] = user.id  # Store user ID in session
                messages.success(request, 'Login successful.')
                return redirect('user_dashboard')  # Redirect to user dashboard
            else:
                messages.error(request, 'Invalid login credentials. Please try again.')
        except PublicUser.DoesNotExist:
            messages.error(request, 'Invalid login credentials. Please try again.')

    return render(request, 'user_login.html')


# Police Station Login
def police_station_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Get email instead of contact
        password = request.POST.get('password')

        try:
            police_station = PoliceStation.objects.get(email=email)  # Lookup using email
            
            # Check if the police station is approved
            if not police_station.approved:
                messages.error(request, 'Your account has not been approved by the admin yet.')
                return redirect('police_station_login')

            if check_password(password, police_station.password):
                request.session['police_station_id'] = police_station.id  # Store police station ID in session
                messages.success(request, 'Login successful as Police Station.')
                return redirect('police_station_dashboard')
            else:
                messages.error(request, 'Invalid login credentials. Please try again.')
        except PoliceStation.DoesNotExist:
            messages.error(request, 'Invalid login credentials. Please try again.')

    return render(request, 'police_station_login.html')



# Public User Dashboard View
def user_dashboard(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        messages.error(request, "You must be logged in to access the dashboard.")
        response = redirect('login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the logged-in user
    user = get_object_or_404(PublicUser, id=request.session['user_id'])
    
    # Get user's complaints
    complaints = Complaint.objects.filter(user=user).order_by('-registered_at')
    
    # Get complaints with FIRs
    complaints_with_fir = complaints.filter(fir__isnull=False)
    
    # Get pending, approved, rejected, and resolved complaints
    pending_complaints = complaints.filter(status='pending').count()
    approved_complaints = complaints.filter(status='approved').count()
    rejected_complaints = complaints.filter(status='rejected').count()
    resolved_complaints = complaints.filter(status='resolved').count()
    
    # Limit complaints to 5 for display
    recent_complaints = complaints[:5]
    
    # Prepare data for pie chart
    status_data = {
        'labels': ['Pending', 'Approved', 'Rejected', 'Resolved'],
        'data': [pending_complaints, approved_complaints, rejected_complaints, resolved_complaints],
        'colors': ['#FFC107', '#4CAF50', '#F44336', '#2196F3']
    }
    
    context = {
        'user': user,
        'complaints': recent_complaints,
        'complaints_with_fir': complaints_with_fir,
        'total_complaints': complaints.count(),
        'pending_complaints': pending_complaints,
        'approved_complaints': approved_complaints,
        'rejected_complaints': rejected_complaints,
        'resolved_complaints': resolved_complaints,
        'status_data': json.dumps(status_data)
    }
    
    return render(request, 'user_dashboard.html', context)


# Police Station Dashboard View
def police_station_dashboard(request):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to access the dashboard.")
        response = redirect('police_station_login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    # Fetch the logged-in police station details
    police_station = get_object_or_404(PoliceStation, id=request.session['police_station_id'])
    
    # Get complaints for this police station
    complaints = Complaint.objects.filter(police_station=police_station)
    
    # Get total counts
    total_complaints = complaints.count()
    pending_complaints = complaints.filter(status='Pending').count()
    under_investigation = complaints.filter(status='Under Investigation').count()
    rejected_complaints = complaints.filter(status='Rejected').count()
    resolved_complaints = complaints.filter(status='Resolved').count()
    
    # Count FIRs filed
    firs_filed = complaints.filter(fir__isnull=False).count()
    
    # Get recent activity logs
    recent_logs = ComplaintLog.objects.filter(complaint__police_station=police_station).order_by('-created_at')[:5]
    
    # Prepare context data
    context = {
        'police_station': police_station,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'rejected_complaints': rejected_complaints,
        'resolved_complaints': resolved_complaints,
        'under_investigation': under_investigation,
        'firs_filed': firs_filed,
        'recent_logs': recent_logs
    }
    
    return render(request, 'police_station_dashboard.html', context)


# Police Station Analytics View
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
import json
from datetime import datetime, timedelta

def police_station_analytics(request):
    if 'police_station_id' not in request.session:
        messages.error(request, 'Please login to access analytics')
        return redirect('police_station_login')
    
    police_station_id = request.session['police_station_id']
    police_station = PoliceStation.objects.get(id=police_station_id)
    
    # Get complaints for this police station
    complaints = Complaint.objects.filter(police_station=police_station)
    
    # Get total counts
    total_complaints = complaints.count()
    pending_complaints = complaints.filter(status='pending').count()
    rejected_complaints = complaints.filter(status='rejected').count()
    approved_complaints = complaints.filter(status='approved').count()
    resolved_complaints = complaints.filter(status='resolved').count()
    
    # Get complaints with FIRs
    complaints_with_fir = complaints.filter(fir__isnull=False).count()
    
    # Complaint types distribution
    complaint_types = complaints.values('complaint_type').annotate(count=Count('id'))
    
    # Monthly complaint trend (last 12 months)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    monthly_trend = complaints.filter(
        registered_at__date__gte=start_date,
        registered_at__date__lte=end_date
    ).annotate(
        month=TruncMonth('registered_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Convert QuerySet to format suitable for charts
    months_data = [
        {
            'month': item['month'].strftime('%b %Y'),
            'count': item['count']
        } for item in monthly_trend
    ]
    
    # Weekly trend (last 10 weeks)
    weekly_start = end_date - timedelta(weeks=10)
    weekly_trend = complaints.filter(
        registered_at__date__gte=weekly_start,
        registered_at__date__lte=end_date
    ).annotate(
        week=TruncWeek('registered_at')
    ).values('week').annotate(
        count=Count('id')
    ).order_by('week')
    
    weeks_data = [
        {
            'week': item['week'].strftime('%d %b'),
            'count': item['count']
        } for item in weekly_trend
    ]
    
    # Daily trend (last 14 days)
    daily_start = end_date - timedelta(days=14)
    daily_trend = complaints.filter(
        registered_at__date__gte=daily_start,
        registered_at__date__lte=end_date
    ).annotate(
        day=TruncDay('registered_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    days_data = [
        {
            'day': item['day'].strftime('%d %b'),
            'count': item['count']
        } for item in daily_trend
    ]
    
    # Average resolution time
    resolved_cases = complaints.filter(status='resolved')
    resolution_times = []
    
    for complaint in resolved_cases:
        # Find the resolution date from complaint logs
        try:
            resolution_log = ComplaintLog.objects.filter(
                complaint=complaint,
                action='Resolved'
            ).order_by('-timestamp').first()
            
            if resolution_log:
                resolution_date = resolution_log.timestamp
                filing_date = complaint.registered_at
                resolution_time = (resolution_date - filing_date).days
                resolution_times.append(resolution_time)
        except Exception as e:
            print(f"Error calculating resolution time: {e}")
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    context = {
        'police_station': police_station,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'rejected_complaints': rejected_complaints,
        'approved_complaints': approved_complaints,
        'resolved_complaints': resolved_complaints,
        'complaints_with_fir': complaints_with_fir,
        'complaint_types': list(complaint_types),
        'months_data': months_data,
        'weeks_data': weeks_data,
        'days_data': days_data,
        'avg_resolution_time': round(avg_resolution_time, 1)
    }
    
    return render(request, 'police_station_analytics.html', context)


# User Logout
def user_logout(request):
    # Clear all session data
    request.session.flush()
    
    # Add success message
    messages.success(request, "You have successfully logged out.")
    
    # Redirect to login page with cache control headers
    response = redirect('login')
    
    # Add no-cache headers
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

# Police Station Logout
def police_station_logout(request):
    # Clear all session data
    request.session.flush()
    
    # Add success message
    messages.success(request, "You have successfully logged out as Police Station.")
    
    # Redirect to login page with cache control headers
    response = redirect('login')
    
    # Add no-cache headers
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

# Add Complaint View
# Add Complaint View
def add_complaint(request):
    if 'user_id' not in request.session:
        messages.error(request, 'You must be logged in to file a complaint.')
        response = redirect('login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the logged-in user
    user = get_object_or_404(PublicUser, id=request.session['user_id'])
    
    # Get all registered police station districts and locations
    police_stations = PoliceStation.objects.filter(approved=True)
    districts = sorted(set([ps.district for ps in police_stations]))
    
    context = {
        'districts': districts,
        'complaint_types': Complaint.COMPLAINT_TYPES,
        'time_choices': Complaint.TIME_CHOICES,
        'today': date.today().strftime('%Y-%m-%d'),
    }
    
    if request.method == 'POST':
        district = request.POST.get('district')
        location = request.POST.get('location')
        complaint_type = request.POST.get('complaint_type')
        description = request.POST.get('description')
        incident_location = request.POST.get('incident_location')  # Get incident location
        incident_date = request.POST.get('incident_date')
        incident_time = request.POST.get('incident_time')
        
        # Validate required fields
        if not all([district, location, complaint_type, description, incident_location, incident_date, incident_time]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'add_complaint.html', context)
        
        try:
            # Get the selected police station
            police_station = PoliceStation.objects.get(district=district, location=location, approved=True)
            
            # Create new complaint
            complaint = Complaint(
                user=user,
                police_station=police_station,
                complaint_type=complaint_type,
                description=description,
                incident_location=incident_location,  # Save incident location
                incident_date=incident_date,
                incident_time=incident_time,
                status='Pending'
            )
            
            # Handle evidence file if uploaded
            if 'evidence' in request.FILES:
                complaint.evidence = request.FILES['evidence']
            
            complaint.save()
            
            # Create log entry for new complaint registration
            ComplaintLog.objects.create(
                complaint=complaint,
                action='Registered',
                details='New complaint registered',
                created_by=f'User ID: {user.id}'
            )
            
            messages.success(request, 'Your complaint has been registered successfully.')
            return redirect('user_dashboard')  # Redirect to dashboard
            
        except PoliceStation.DoesNotExist:
            messages.error(request, 'Selected police station not found.')
        except Exception as e:
            messages.error(request, f'Error registering complaint: {str(e)}')
    
    return render(request, 'add_complaint.html', context)

# Get Locations AJAX View
def get_locations(request):
    district = request.GET.get('district', '')
    locations = []
    
    if district:
        police_stations = PoliceStation.objects.filter(district=district, approved=True)
        locations = sorted(set([ps.location for ps in police_stations]))
    
    return JsonResponse({'locations': locations})

# View Complaints View
def view_complaints(request):
    if 'user_id' not in request.session:
        messages.error(request, 'You must be logged in to view your complaints.')
        response = redirect('login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the logged-in user
    user = get_object_or_404(PublicUser, id=request.session['user_id'])
    
    # Get all complaints registered by this user
    complaints = Complaint.objects.filter(user=user).order_by('-registered_at')
    
    return render(request, 'view_complaints.html', {
        'user': user,
        'complaints': complaints
    })

# Add this to your views.py file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import PoliceStation, Complaint, PublicUser

def police_view_complaints(request):
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to access the complaints.")
        response = redirect('police_station_login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the logged-in police station
    police_station = get_object_or_404(PoliceStation, id=request.session['police_station_id'])
    
    # Get only new (pending) complaints registered for this police station
    complaints = Complaint.objects.filter(
        police_station=police_station,
        status='Pending'
    ).order_by('-registered_at')
    
    # Add filter option to show all complaints if requested
    show_all = request.GET.get('show_all', 'false').lower() == 'true'
    if show_all:
        complaints = Complaint.objects.filter(
            police_station=police_station
        ).order_by('-registered_at')
    
    return render(request, 'police_view_complaints.html', {
        'police_station': police_station,
        'complaints': complaints,
        'show_all': show_all
    })

def update_complaint_status(request, complaint_id, action):
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to update complaints.")
        response = redirect('police_station_login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the complaint and make sure it belongs to this police station
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        police_station_id=request.session['police_station_id']
    )
    
    # Update complaint status based on action
    if action == 'approve':
        complaint.status = 'Under Investigation'
        complaint.save()
        
        # Create log entry for this action
        ComplaintLog.objects.create(
            complaint=complaint,
            action='Approved',
            details='Complaint approved for investigation',
            created_by=f'Police Station ID: {request.session["police_station_id"]}'
        )
        
        # Send email to the user
        # Send approval email
        send_html_email(
            subject='Your Complaint Has Been Approved - Safe Call',
            template_name='core/emails/complaint_approved.html',
            context={
                'user_name': f'{complaint.user.first_name} {complaint.user.last_name}',
                'complaint_id': complaint.id,
                'complaint_type': complaint.complaint_type,
                'incident_date': complaint.incident_date,
                'incident_time': complaint.incident_time,
                'registered_at': complaint.registered_at.strftime('%Y-%m-%d %H:%M'),
                'police_station': complaint.police_station.location,
                'district': complaint.police_station.district,
                'police_contact': complaint.police_station.contact,
                'login_url': request.build_absolute_uri('/login/')
            },
            recipient_list=[complaint.user.email]
        )
        
        messages.success(request, f"Complaint #{complaint.id} has been approved and is now under investigation.")
    
    elif action == 'reject':
        complaint.status = 'Rejected'
        complaint.save()
        
        # Create log entry for this action
        ComplaintLog.objects.create(
            complaint=complaint,
            action='Rejected',
            details='Complaint rejected',
            created_by=f'Police Station ID: {request.session["police_station_id"]}'
        )
        
        # Send email to the user
        # Send rejection email
        send_html_email(
            subject='Your Complaint Status Update - Safe Call',
            template_name='core/emails/complaint_rejected.html',
            context={
                'user_name': f'{complaint.user.first_name} {complaint.user.last_name}',
                'complaint_id': complaint.id,
                'complaint_type': complaint.complaint_type,
                'help_center_url': request.build_absolute_uri('/contact/'),
                'police_station': complaint.police_station.location,
                'district': complaint.police_station.district,
                'police_contact': complaint.police_station.contact,
                'incident_date': complaint.incident_date,
                'incident_time': complaint.incident_time,
                'registered_at': complaint.registered_at.strftime('%Y-%m-%d %H:%M')
            },
            recipient_list=[complaint.user.email]
        )
        
        messages.info(request, f"Complaint #{complaint.id} has been rejected.")
    
    # Redirect back to the complaints page
    return redirect('police_view_complaints')

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Complaint, PublicUser, PoliceStation

# New view for viewing FIR
def view_fir(request, complaint_id):
    if 'user_id' not in request.session:
        messages.error(request, 'You must be logged in to view FIR.')
        response = redirect('login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the complaint and make sure it belongs to the logged-in user
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        user_id=request.session['user_id']
    )
    
    return render(request, 'fir_template.html', {'complaint': complaint})

# New view for "downloading" FIR (will open in a new tab for printing)
def download_fir(request, complaint_id):
    if 'user_id' not in request.session:
        messages.error(request, 'You must be logged in to download FIR.')
        response = redirect('login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the complaint and make sure it belongs to the logged-in user
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        user_id=request.session['user_id']
    )
    
    # Render the template with print functionality
    return render(request, 'fir_download_template.html', {'complaint': complaint})

def manage_fir(request):
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to access this page.")
        response = redirect('police_station_login')
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    # Get the logged-in police station
    police_station = get_object_or_404(PoliceStation, id=request.session['police_station_id'])
    
    # Get all complaints for the police station, excluding pending and rejected by default
    complaints = Complaint.objects.filter(police_station=police_station).exclude(
        status__in=['Pending', 'Rejected']
    )
    
    # Individual field search functionality
    search_id = request.GET.get('search_id', '')
    search_name = request.GET.get('search_name', '')
    search_location = request.GET.get('search_location', '')
    search_type = request.GET.get('search_type', '')
    search_description = request.GET.get('search_description', '')
    
    # Apply individual field searches
    if search_id:
        try:
            complaints = complaints.filter(id=int(search_id))
        except ValueError:
            pass  # If search_id is not a valid integer, ignore it
    
    if search_name:
        complaints = complaints.filter(
            Q(user__first_name__icontains=search_name) |
            Q(user__last_name__icontains=search_name)
        )
    
    if search_location:
        complaints = complaints.filter(incident_location__icontains=search_location)
    
    if search_type:
        complaints = complaints.filter(complaint_type__icontains=search_type)
    
    if search_description:
        complaints = complaints.filter(description__icontains=search_description)
    
    # Status filter
    status = request.GET.get('status')
    if status:
        # If status is specified, show all complaints with that status
        complaints = Complaint.objects.filter(police_station=police_station, status=status)
    
    # Complaint type filter
    complaint_type = request.GET.get('complaint_type')
    if complaint_type:
        complaints = complaints.filter(complaint_type=complaint_type)
    
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        complaints = complaints.filter(incident_date__gte=start_date)
    if end_date:
        complaints = complaints.filter(incident_date__lte=end_date)
    
    # Time of day filter
    incident_time = request.GET.get('incident_time')
    if incident_time:
        complaints = complaints.filter(incident_time=incident_time)
    
    # Sorting
    sort_by = request.GET.get('sort')
    if sort_by == 'newest':
        complaints = complaints.order_by('-registered_at')
    elif sort_by == 'oldest':
        complaints = complaints.order_by('registered_at')
    elif sort_by == 'priority':
        complaints = complaints.order_by('-priority')
    else:
        # Default sorting by newest first
        complaints = complaints.order_by('-registered_at')
    
    # Add pagination
    paginator = Paginator(complaints, 10)  # Show 10 complaints per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    status_choices = Complaint.STATUS_CHOICES
    complaint_types = Complaint.COMPLAINT_TYPES
    time_choices = Complaint.TIME_CHOICES
    
    context = {
        'complaints': page_obj,
        'search_id': search_id,
        'search_name': search_name,
        'search_location': search_location,
        'search_type': search_type,
        'search_description': search_description,
        'current_status': status,
        'current_complaint_type': complaint_type,
        'current_incident_time': incident_time,
        'current_sort': sort_by,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': status_choices,
        'complaint_types': complaint_types,
        'time_choices': time_choices,
        'total_results': complaints.count(),
        'today_date': timezone.now(),
    }
    return render(request, 'manage_fir.html', context)

def create_fir(request, complaint_id):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to create FIRs.")
        return redirect('police_station_login')
    
    # Get the complaint and verify it belongs to this police station
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        police_station_id=request.session['police_station_id']
    )
    
    if request.method == 'POST':
        try:
            # Create FIR
            fir = FIR.objects.create(
                complaint=complaint,
                spot_location=request.POST.get('spot_location'),
                police_description=request.POST.get('police_description')
            )
            
            # Handle multiple evidence files
            evidence_files = request.FILES.getlist('additional_evidence[]')
            for evidence_file in evidence_files:
                if evidence_file:
                    FIREvidence.objects.create(
                        fir=fir,
                        file=evidence_file
                    )
            
            # Handle witnesses
            # Get all witness indices from the form data
            witness_indices = set()
            for key in request.POST.keys():
                if key.startswith('witnesses['):
                    # Extract the index from the key (e.g., 'witnesses[0][first_name]' -> '0')
                    index = key.split('[')[1].split(']')[0]
                    witness_indices.add(index)
            
            # Create witnesses for each index
            for index in witness_indices:
                first_name = request.POST.get(f'witnesses[{index}][first_name]')
                last_name = request.POST.get(f'witnesses[{index}][last_name]')
                phone_number = request.POST.get(f'witnesses[{index}][phone_number]')
                
                if first_name and last_name and phone_number:  # Only create if all fields are provided
                    Witness.objects.create(
                        fir=fir,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number
                    )
            
            # Update complaint status to Under Investigation
            complaint.status = 'Under Investigation'
            complaint.save()
            
            # Create log entry for FIR creation
            ComplaintLog.objects.create(
                complaint=complaint,
                action='FIR Filed',
                details=f'FIR filed with {len(evidence_files)} evidence files and {len(witness_indices)} witnesses',
                created_by=f'Police Station ID: {request.session["police_station_id"]}'
            )
            
            messages.success(request, f"FIR has been created successfully for Complaint #{complaint.id}")
            return redirect('manage_fir')
            
        except Exception as e:
            messages.error(request, f"Error creating FIR: {str(e)}")
            return redirect('manage_fir')
    
    return redirect('manage_fir')

def resolve_complaint(request, complaint_id):
    if 'police_station_id' not in request.session:
        messages.error(request, 'Please login to resolve complaints.')
        return redirect('police_station_login')
    
    try:
        complaint = Complaint.objects.get(id=complaint_id, police_station_id=request.session['police_station_id'])
        
        if complaint.status == 'Resolved':
            messages.warning(request, 'This complaint is already resolved.')
            return redirect('manage_fir')
        
        complaint.status = 'Resolved'
        complaint.resolution_date = timezone.now()  # Save the resolution date
        complaint.save()
        
        # Create log entry for resolution
        ComplaintLog.objects.create(
            complaint=complaint,
            action='Resolved',
            details=f'Complaint resolved on {timezone.now().strftime("%Y-%m-%d %H:%M")}',
            created_by=f'Police Station ID: {request.session["police_station_id"]}'
        )
        
        messages.success(request, 'Complaint marked as resolved successfully.')
    except Complaint.DoesNotExist:
        messages.error(request, 'Complaint not found or you do not have permission to resolve it.')
    
    return redirect('manage_fir')

def validate_phone_number(phone_number):
    if not re.match(r'^[0-9]{10}$', phone_number):
        raise ValidationError('Phone number must be exactly 10 digits')

def add_evidence_to_fir(request, complaint_id):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to add evidence.")
        return redirect('police_station_login')
    
    if request.method == 'POST':
        try:
            complaint = Complaint.objects.get(id=complaint_id)
            police_station = PoliceStation.objects.get(id=request.session['police_station_id'])
            
            # Verify police station has jurisdiction
            if complaint.police_station != police_station:
                messages.error(request, 'You do not have jurisdiction over this complaint.')
                return redirect('manage_fir')
            
            evidence_file = request.FILES.get('evidence_file')
            
            # Server-side validation
            if not evidence_file:
                messages.error(request, 'Please select a file to upload.')
                return redirect('manage_fir')
            
            # Validate file size (10MB limit)
            if evidence_file.size > 10 * 1024 * 1024:
                messages.error(request, 'File size must be less than 10MB.')
                return redirect('manage_fir')
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/quicktime', 'application/pdf']
            if evidence_file.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Please upload an image, video, or PDF file.')
                return redirect('manage_fir')
            
            # Create or get FIR
            fir, created = FIR.objects.get_or_create(
                complaint=complaint,
                defaults={
                    'spot_location': complaint.incident_location,
                    'police_description': 'Initial FIR created with evidence.'
                }
            )
            
            # Add evidence
            evidence = FIREvidence.objects.create(
                fir=fir,
                file=evidence_file
            )
            
            # Create log entry for evidence addition
            ComplaintLog.objects.create(
                complaint=complaint,
                action='Evidence Added',
                details=f'Evidence file added: {evidence_file.name}',
                created_by=f'Police Station ID: {request.session["police_station_id"]}'
            )
            
            # Update complaint status if needed
            if complaint.status == 'Pending':
                complaint.status = 'Under Investigation'
                complaint.save()
            
            messages.success(request, 'Evidence added successfully.')
            
        except Complaint.DoesNotExist:
            messages.error(request, 'Complaint not found.')
        except PoliceStation.DoesNotExist:
            messages.error(request, 'Police station not found.')
        except Exception as e:
            messages.error(request, f"Error adding evidence: {str(e)}")
        
        return redirect('manage_fir')

def add_witness_to_fir(request, complaint_id):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to add witnesses.")
        return redirect('police_station_login')
    
    if request.method == 'POST':
        try:
            complaint = Complaint.objects.get(id=complaint_id)
            police_station = PoliceStation.objects.get(id=request.session['police_station_id'])
            
            # Verify police station has jurisdiction
            if complaint.police_station != police_station:
                messages.error(request, 'You do not have jurisdiction over this complaint.')
                return redirect('manage_fir')
            
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            
            # Server-side validation
            if not first_name or len(first_name) < 2:
                messages.error(request, 'First name must be at least 2 characters long.')
                return redirect('manage_fir')
            
            if not last_name or len(last_name) < 2:
                messages.error(request, 'Last name must be at least 2 characters long.')
                return redirect('manage_fir')
            
            try:
                validate_phone_number(phone_number)
            except ValidationError:
                messages.error(request, 'Please enter a valid 10-digit phone number.')
                return redirect('manage_fir')
            
            # Create or get FIR
            fir, created = FIR.objects.get_or_create(
                complaint=complaint,
                defaults={
                    'spot_location': complaint.incident_location,
                    'police_description': 'Initial FIR created with witness.'
                }
            )
            
            # Add witness
            witness = Witness.objects.create(
                fir=fir,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            
            # Create log entry for witness addition
            ComplaintLog.objects.create(
                complaint=complaint,
                action='Witness Added',
                details=f'Witness added: {first_name} {last_name}',
                created_by=f'Police Station ID: {request.session["police_station_id"]}'
            )
            
            # Update complaint status if needed
            if complaint.status == 'Pending':
                complaint.status = 'Under Investigation'
                complaint.save()
            
            messages.success(request, 'Witness added successfully.')
            
        except Complaint.DoesNotExist:
            messages.error(request, 'Complaint not found.')
        except PoliceStation.DoesNotExist:
            messages.error(request, 'Police station not found.')
        except Exception as e:
            messages.error(request, f"Error adding witness: {str(e)}")
        
        return redirect('manage_fir')

def get_applicable_legal_sections(complaint_type):
    """
    Returns applicable legal sections based on the complaint type using Bharatiya Nyaya Sanhita (BNS)
    which replaced the Indian Penal Code (IPC) in July 2024
    """
    legal_sections = {
        'Robbery': [
            {'section': '302', 'description': 'Robbery - Theft with use of force or fear of force'},
            {'section': '303', 'description': 'Punishment for robbery - Imprisonment up to 10 years and fine'},
            {'section': '307', 'description': 'Voluntarily causing hurt in committing robbery - Imprisonment up to 10 years and fine'}
        ],
        'Assault': [
            {'section': '126', 'description': 'Assault - Gesture or preparation to apply criminal force'},
            {'section': '127', 'description': 'Punishment for assault - Imprisonment up to 3 months, or fine, or both'},
            {'section': '115', 'description': 'Punishment for voluntarily causing hurt - Imprisonment up to 1 year, or fine, or both'}
        ],
        'Threats': [
            {'section': '351', 'description': 'Criminal intimidation - Threatening with injury to person, reputation or property'},
            {'section': '352', 'description': 'Punishment for criminal intimidation - Imprisonment up to 2 years, or fine, or both'}
        ],
        'Burglary': [
            {'section': '309', 'description': 'House-breaking - Breaking into a building to commit an offense'},
            {'section': '310', 'description': 'Punishment for house-breaking - Imprisonment up to 3 years and fine'},
            {'section': '311', 'description': 'House-breaking by night - Imprisonment up to 5 years and fine'}
        ],
        'Vandalism': [
            {'section': '295', 'description': 'Mischief - Causing wrongful loss or damage to property'},
            {'section': '296', 'description': 'Punishment for mischief - Imprisonment up to 3 months, or fine, or both'}
        ],
        'Fraud': [
            {'section': '318', 'description': 'Cheating - Fraudulently deceiving a person to deliver property or consent'},
            {'section': '319', 'description': 'Cheating and dishonestly inducing delivery of property - Imprisonment up to 7 years and fine'}
        ],
        'Harassment': [
            {'section': '78', 'description': 'Sexual harassment - Unwelcome physical contact, demand for sexual favors, etc.'},
            {'section': '79', 'description': 'Stalking - Following a person and contacting despite disinterest'},
            {'section': '356', 'description': 'Word, gesture or act intended to insult the modesty of a woman - Imprisonment up to 3 years and fine'}
        ],
        'Theft': [
            {'section': '303', 'description': 'Theft - Dishonestly taking movable property without consent'},
            {'section': '304', 'description': 'Punishment for theft - Imprisonment up to 3 years, or fine, or both'}
        ],
        'Domestic Violence': [
            {'section': '85', 'description': 'Cruelty by husband or relative of husband - Imprisonment up to 3 years and fine'},
            {'section': 'DV Act', 'description': 'Protection of Women from Domestic Violence Act, 2005 (still applicable)'}
        ],
        'Sexual Assault': [
            {'section': '65', 'description': 'Rape - Sexual assault without consent'},
            {'section': '66', 'description': 'Punishment for rape - Rigorous imprisonment not less than 10 years, may extend to life imprisonment and fine'}
        ],
        'Kidnapping': [
            {'section': '136', 'description': 'Kidnapping - Taking or enticing a person without consent'},
            {'section': '137', 'description': 'Punishment for kidnapping - Imprisonment up to 7 years and fine'}
        ],
        'Stalking': [
            {'section': '79', 'description': 'Stalking - Following a person and contacting despite disinterest - Imprisonment up to 3 years for first conviction'}
        ],
        'Drunk Driving': [
            {'section': 'BNSS 162', 'description': 'Driving by a drunken person or by a person under the influence of drugs - Imprisonment up to 6 months, or fine, or both'}
        ],
        'Hit and Run': [
            {'section': '106', 'description': 'Rash driving or riding on a public way - Imprisonment up to 6 months, or fine, or both'},
            {'section': '105', 'description': 'Causing death by negligence - Imprisonment up to 5 years, or fine, or both'}
        ],
        'Drug Offenses': [
            {'section': 'NDPS Act', 'description': 'Possession, sale, purchase, or use of narcotic drugs and psychotropic substances - Varies based on quantity and substance (NDPS Act still applicable)'}
        ],
        'Public Intoxication': [
            {'section': '296', 'description': 'Misconduct in public by a drunken person - Imprisonment up to 24 hours, or fine, or both'}
        ],
        'Trespassing': [
            {'section': '314', 'description': 'Criminal trespass - Entering property with intent to commit an offense'},
            {'section': '315', 'description': 'Punishment for criminal trespass - Imprisonment up to 3 months, or fine, or both'}
        ],
        'Hate Crimes': [
            {'section': '195', 'description': 'Promoting enmity between different groups on grounds of religion, race, place of birth, residence, language, etc. - Imprisonment up to 3 years, or fine, or both'}
        ],
        'Murder': [
            {'section': '103', 'description': 'Murder - Causing death with the intention of causing death'},
            {'section': '103(1)', 'description': 'Punishment for murder - Death or imprisonment for life, and fine'}
        ],
        'Arson': [
            {'section': '298', 'description': 'Mischief by fire or explosive substance with intent to cause damage - Imprisonment up to 7 years and fine'},
            {'section': '299', 'description': 'Mischief by fire or explosive substance with intent to destroy house, etc. - Imprisonment up to 10 years and fine'}
        ],
        'Others': [
            {'section': 'Various', 'description': 'Applicable sections will be determined based on specific details of the complaint'}
        ]
    }
    
    return legal_sections.get(complaint_type, [])

def view_case_file(request, complaint_id):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to view case files.")
        return redirect('police_station_login')
    
    # Get the complaint and verify it belongs to this police station
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        police_station_id=request.session['police_station_id']
    )
    
    # Get applicable legal sections based on complaint type
    legal_sections = get_applicable_legal_sections(complaint.complaint_type)
    
    return render(request, 'case_file_report.html', {
        'complaint': complaint,
        'legal_sections': legal_sections
    })

def add_description_to_fir(request, complaint_id):
    # Check if police station is logged in
    if 'police_station_id' not in request.session:
        messages.error(request, "You must be logged in as a police station to add descriptions to FIRs.")
        return redirect('police_station_login')
    
    # Get the complaint and verify it belongs to this police station
    complaint = get_object_or_404(
        Complaint, 
        id=complaint_id, 
        police_station_id=request.session['police_station_id']
    )
    
    # Check if FIR exists
    if not hasattr(complaint, 'fir'):
        messages.error(request, "FIR does not exist for this complaint.")
        return redirect('manage_fir')
    
    if request.method == 'POST':
        description = request.POST.get('additional_description', '').strip()
        
        # Validate description
        if not description:
            messages.error(request, "Description cannot be empty.")
        elif len(description) < 10:
            messages.error(request, "Description is too short. Please provide at least 10 characters.")
        elif len(description) > 5000:
            messages.error(request, "Description is too long. Please limit to 5000 characters.")
        else:
            # Create new description entry
            FIRDescription.objects.create(
                fir=complaint.fir,
                description=description
            )
            messages.success(request, "Additional description added successfully.")
    
    return redirect('manage_fir')

def contact(request):
    return render(request, 'contact.html')

# Password Reset Views
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')
        
        # Check if email exists based on user type
        user = None
        if user_type == 'public':
            user = PublicUser.objects.filter(email=email).first()
        elif user_type == 'police':
            user = PoliceStation.objects.filter(email=email).first()
            
        if user:
            # Generate and save OTP
            otp = generate_otp()
            PasswordResetToken.objects.create(
                email=email,
                token=otp,
                user_type=user_type
            )
            
            # Send OTP via email
            subject = 'Password Reset OTP - Safe Call'
            message = f'Your OTP for password reset is: {otp}\nThis OTP will expire in 10 minutes.'
            # Send password reset email
            send_html_email(
                subject=subject,
                template_name='core/emails/password_reset.html',
                context={
                    'otp': otp,
                    'login_url': request.build_absolute_uri('/login/')
                },
                recipient_list=[email],
                fail_silently=False
            )
            
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('verify_reset_otp')
        else:
            messages.error(request, 'Email not found.')
            
    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        
        # Find valid token
        token = PasswordResetToken.objects.filter(
            email=email,
            token=otp,
            is_used=False
        ).order_by('-created_at').first()
        
        if token and token.is_valid():
            # Update password based on user type
            try:
                if token.user_type == 'public':
                    user = PublicUser.objects.get(email=email)
                    success_url = 'user_login'
                else:
                    user = PoliceStation.objects.get(email=email)
                    success_url = 'police_station_login'
                    
                user.password = make_password(new_password)
                user.save()
                
                # Mark token as used
                token.is_used = True
                token.save()
                
                messages.success(request, 'Password has been reset successfully. Please login with your new password.')
                return redirect(success_url)
            except (PublicUser.DoesNotExist, PoliceStation.DoesNotExist):
                messages.error(request, 'User not found.')
        else:
            messages.error(request, 'Invalid or expired OTP.')
            
    return render(request, 'verify_reset_otp.html')

@csrf_exempt
def create_donation_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        amount = int(float(data.get('amount', 0)) * 100)  # Convert to paise
        name = data.get('name', '')
        email = data.get('email', '')
        payment_method = data.get('payment_method', 'upi')

        # Validate amount
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'})

        # Create Razorpay Order
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,  # Auto capture payment
            'notes': {
                'name': name,
                'email': email,
                'payment_method': payment_method
            }
        }
        
        order = razorpay_client.order.create(order_data)
        
        # Try to find a PublicUser with the provided email
        user = None
        if request.user.is_authenticated and hasattr(request.user, 'publicuser'):
            user = request.user.publicuser
        else:
            try:
                user = PublicUser.objects.get(email=email)
            except PublicUser.DoesNotExist:
                pass  # It's okay if we don't find a user
        
        # Create donation record
        donation = Donation.objects.create(
            user=user,  # This can be None if no matching user is found
            donor_name=name,
            donor_email=email,
            amount=float(amount) / 100,
            order_id=order['id'],
            payment_status='pending',
            payment_response={
                'name': name,
                'email': email,
                'payment_method': payment_method
            }
        )
        
        return JsonResponse({
            'order_id': order['id'],
            'amount': amount,
            'currency': 'INR',
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'prefill': {
                'name': name,
                'email': email
            }
        })
        
    except Exception as e:
        print(f"Error creating donation order: {str(e)}")  # For debugging
        return JsonResponse({'error': str(e)})

@csrf_exempt
def verify_donation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})

    try:
        # Get payment data
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            # Verify signature
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Get payment details
            payment = razorpay_client.payment.fetch(razorpay_payment_id)
            
            # Update donation record
            donation = Donation.objects.get(order_id=razorpay_order_id)
            donation.payment_id = razorpay_payment_id
            donation.payment_status = 'successful'
            donation.payment_response = {
                **params_dict,
                'payment_method': payment.get('method', ''),
                'vpa': payment.get('vpa', ''),  # UPI ID if paid via UPI
                'payment_details': payment
            }
            donation.save()
            
            # Send success invoice email
            try:
                send_donation_invoice(
                    donor_name=donation.donor_name,
                    donor_email=donation.donor_email,
                    amount=donation.amount,
                    order_id=donation.order_id,
                    transaction_id=donation.payment_id,
                    payment_method=payment.get('method', 'Online Payment'),
                    status='Success',
                    receipt_url=request.build_absolute_uri(f'/donation-details/{donation.id}/')
                )
                print(f"Success invoice email sent to {donation.donor_email}")
            except Exception as email_error:
                print(f"Error sending success invoice email: {str(email_error)}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment verified successfully'
            })
            
        except Exception as e:
            # Signature verification failed
            donation = Donation.objects.get(order_id=razorpay_order_id)
            donation.payment_status = 'failed'
            donation.payment_response = {
                'error': str(e),
                'payment_id': razorpay_payment_id
            }
            donation.save()
            
            # Send failure invoice email
            try:
                send_donation_invoice(
                    donor_name=donation.donor_name,
                    donor_email=donation.donor_email,
                    amount=donation.amount,
                    order_id=donation.order_id,
                    transaction_id=razorpay_payment_id or 'N/A',
                    payment_method='Online Payment',
                    status='Failed',
                    receipt_url=None
                )
                print(f"Failed payment invoice email sent to {donation.donor_email}")
            except Exception as email_error:
                print(f"Error sending failed invoice email: {str(email_error)}")
            
            return JsonResponse({
                'status': 'failed',
                'error': 'Payment verification failed'
            })
            
    except Exception as e:
        print(f"Error verifying donation: {str(e)}")  # For debugging
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })

def donate(request):
    # Get statistics for impact section
    stats = {
        'total_cases': Complaint.objects.count(),
        'resolved_cases': Complaint.objects.filter(status='Resolved').count(),
        'total_users': PublicUser.objects.count()
    }
    
    return render(request, 'core/donate.html', {
        'stats': stats,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    })

def donation_details(request, donation_id):
    try:
        donation = Donation.objects.get(id=donation_id)
        return JsonResponse({
            'created_at': donation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'name': donation.donor_name or 'Anonymous',
            'email': donation.donor_email or 'N/A',
            'amount': donation.amount,
            'payment_method': donation.payment_response.get('method', 'N/A') if donation.payment_response else 'N/A',
            'payment_id': donation.payment_id or 'N/A',
            'order_id': donation.order_id or 'N/A',
            'status': donation.payment_status,
            'payment_response': donation.payment_response or {}
        })
    except Donation.DoesNotExist:
        return JsonResponse({'error': 'Donation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_police)
def get_complete_report(request, complaint_id):
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        fir = complaint.fir  # Get associated FIR
        evidence = FIREvidence.objects.filter(fir=fir) if hasattr(complaint, 'fir') else []
        witnesses = Witness.objects.filter(fir=fir) if hasattr(complaint, 'fir') else []
        
        # Get additional descriptions if they exist
        additional_descriptions = FIRDescription.objects.filter(fir=fir) if hasattr(complaint, 'fir') else []
        
        # Serialize the data
        data = {
            'id': complaint.id,
            'complaint_type': complaint.get_complaint_type_display(),
            'description': complaint.description,
            'location': complaint.incident_location,
            'incident_date': complaint.incident_date.strftime('%d %b %Y'),
            'incident_time': complaint.get_incident_time_display(),
            'status': complaint.get_status_display(),
            'date_reported': complaint.registered_at.strftime('%d %b %Y, %I:%M %p'),
            'date_resolved': complaint.resolution_date.strftime('%d %b %Y, %I:%M %p') if complaint.resolution_date else None,
            'user': {
                'first_name': complaint.user.first_name,
                'last_name': complaint.user.last_name,
                'email': complaint.user.email,
                'phone': complaint.user.phone,
                'adhaar': complaint.user.adhaar,
                'date_of_birth': complaint.user.date_of_birth.strftime('%d %b %Y') if complaint.user.date_of_birth else None,
                'gender': complaint.user.get_gender_display() if complaint.user.gender else None,
                'address': complaint.user.address,
                'district': complaint.user.district,
                'pincode': complaint.user.pincode,
            },
            'evidence': [{
                'file': ev.file.url if ev.file else None,
                'uploaded_at': ev.uploaded_at.strftime('%d %b %Y, %I:%M %p')
            } for ev in evidence],
            'witnesses': [{
                'name': f"{w.first_name} {w.last_name}",
                'phone': w.phone_number,
                'added_at': w.created_at.strftime('%d %b %Y, %I:%M %p')
            } for w in witnesses],
            'additional_descriptions': [{
                'description': desc.description,
                'created_at': desc.created_at.strftime('%d %b %Y, %I:%M %p')
            } for desc in additional_descriptions],
            'police_station': {
                'name': complaint.police_station.location,
                'district': complaint.police_station.district,
                'contact': complaint.police_station.contact
            }
        }
        
        return JsonResponse(data)
    except Complaint.DoesNotExist:
        return JsonResponse({'error': 'Complaint not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def debug_info(request):
    """
    View for debugging deployment issues.
    Returns system information, request data, and environment.
    """
    # Only allow in DEBUG mode or with specific parameter for security
    if not settings.DEBUG and request.GET.get('debug_key') != 'SafeCallDebug123':
        return JsonResponse({"error": "Debug view not available in production"}, status=403)

    # Collect debug information
    debug_data = {
        "system_info": {
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "request_data": {
            "path": request.path,
            "method": request.method,
            "content_type": request.content_type,
            "META": {k: str(v) for k, v in request.META.items() if k.startswith('HTTP_')},
        },
        "settings": {
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "database_engine": settings.DATABASES['default']['ENGINE'],
            "static_root": settings.STATIC_ROOT,
            "static_url": settings.STATIC_URL,
        }
    }
    
    return JsonResponse(debug_data)