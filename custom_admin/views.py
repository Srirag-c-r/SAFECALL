from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import PublicUser, PoliceStation, Complaint, ComplaintLog, Donation
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from datetime import datetime, timezone, timedelta

class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

import csv
from django.urls import reverse_lazy
from django.views.generic import View

class DashboardView(SuperUserRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Get public user statistics
            from core.models import PublicUser
            context['user_count'] = PublicUser.objects.filter(is_verified=True).count()

            # Get complaint statistics
            from core.models import Complaint, PoliceStation, FIR
            
            # Active complaints - only include Pending and Under Investigation
            active_complaints = Complaint.objects.filter(
                status__in=['Pending', 'Under Investigation']
            ).count()
            context['active_complaints'] = active_complaints

            # Only count approved police stations
            active_stations = PoliceStation.objects.filter(approved=True).count()
            context['police_stations'] = active_stations

            # Count FIRs with proper relationships
            firs_count = FIR.objects.select_related('complaint').count()
            context['firs_filed'] = firs_count

            # Get recent complaints with all related data
            recent_complaints = Complaint.objects.select_related(
                'user',
                'police_station'
            ).order_by(
                '-registered_at'
            )[:10]

            complaints_data = []
            for complaint in recent_complaints:
                try:
                    complaints_data.append({
                        'id': complaint.id,
                        'complainant': f"{complaint.user.first_name} {complaint.user.last_name}".strip(),
                        'type': complaint.complaint_type,
                        'status': complaint.status,
                        'status_color': self.get_status_color(complaint.status),
                        'date': complaint.registered_at.strftime('%Y-%m-%d'),
                        'police_station': complaint.police_station.location if complaint.police_station else 'Not Assigned'
                    })
                except Exception as e:
                    print(f"Error processing complaint {complaint.id}: {str(e)}")
                    continue

            context['recent_complaints'] = complaints_data

        except Exception as e:
            print(f"Error in dashboard: {str(e)}")
            # Set default values in case of errors
            context.update({
                'user_count': 0,
                'active_complaints': 0,
                'police_stations': 0,
                'firs_filed': 0,
                'recent_complaints': []
            })

        # Get complaint type statistics
        complaint_types = Complaint.objects.values('complaint_type').annotate(
            count=Count('id')
        ).order_by('-count')

        total_complaints = Complaint.objects.count()
        context['complaint_stats'] = [
            {
                'type': ct['complaint_type'],
                'count': ct['count'],
                'percentage': (ct['count'] / total_complaints * 100) if total_complaints > 0 else 0
            } for ct in complaint_types
        ]

        # Add download report URL
        context['download_report_url'] = reverse_lazy('custom_admin:download_report')

        return context

    def get_status_color(self, status):
        status_colors = {
            'Pending': 'warning',
            'In Progress': 'info',
            'FIR Filed': 'primary',
            'Resolved': 'success',
            'Rejected': 'danger'
        }
        return status_colors.get(status, 'secondary')

class DownloadReportView(SuperUserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with CSV header
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="safecall_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'},
        )

        # Create CSV writer
        writer = csv.writer(response)

        # Write headers
        writer.writerow(['Report Type', 'Count'])

        # Get statistics
        User = get_user_model()
        from core.models import Complaint, PoliceStation

        # Write statistics
        writer.writerow(['Total Users', User.objects.count()])
        writer.writerow(['Active Complaints', Complaint.objects.filter(status='Pending').count()])
        writer.writerow(['Police Stations', PoliceStation.objects.count()])
        writer.writerow(['FIRs Filed', Complaint.objects.filter(status='FIR Filed').count()])
        writer.writerow([])

        # Write complaint type statistics
        writer.writerow(['Complaint Type', 'Count', 'Percentage'])
        complaint_types = Complaint.objects.values('complaint_type').annotate(
            count=Count('id')
        ).order_by('-count')

        total_complaints = Complaint.objects.count()
        for ct in complaint_types:
            percentage = (ct['count'] / total_complaints * 100) if total_complaints > 0 else 0
            writer.writerow([ct['complaint_type'], ct['count'], f'{percentage:.1f}%'])

        return response

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password

class UserListView(SuperUserRequiredMixin, TemplateView):
    template_name = 'admin/users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            filter_type = self.request.GET.get('filter', 'all')

            # Get public users with filter
            public_users = PublicUser.objects.all()
            if filter_type == 'verified':
                public_users = public_users.filter(is_verified=True)
            elif filter_type == 'new':
                public_users = public_users.filter(is_verified=False)

            # Get police stations
            police_stations = PoliceStation.objects.all().order_by('district', 'location')

            context.update({
                'public_users': public_users,
                'police_stations': police_stations,
                'current_filter': filter_type
            })
        except Exception as e:
            messages.error(self.request, f'Error loading users: {str(e)}')
            context.update({
                'public_users': [],
                'police_stations': [],
                'current_filter': 'all'
            })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user_type = request.POST.get('user_type')

        try:
            if user_type == 'public':
                user = PublicUser.objects.get(id=user_id)
                if action == 'verify':
                    user.is_verified = True
                    user.save()
                    messages.success(request, f'User {user.email} has been verified.')
                elif action == 'suspend':
                    user.is_verified = False
                    user.save()
                    messages.success(request, f'User {user.email} has been suspended.')
            elif user_type == 'police':
                station = PoliceStation.objects.get(id=user_id)
                if action == 'approve':
                    station.approved = True
                    station.save()
                    messages.success(request, f'Police station {station.location} has been approved.')
                elif action == 'suspend':
                    station.approved = False
                    station.save()
                    messages.success(request, f'Police station {station.location} has been suspended.')

        except (PublicUser.DoesNotExist, PoliceStation.DoesNotExist):
            messages.error(request, 'User or police station not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('custom_admin:users')

@method_decorator(require_http_methods(['POST']), name='dispatch')
class AddPoliceStationView(SuperUserRequiredMixin, View):
    def post(self, request):
        try:
            # Get form data
            data = {
                'district': request.POST.get('district'),
                'location': request.POST.get('location'),
                'pincode': request.POST.get('pincode'),
                'contact': request.POST.get('contact'),
                'email': request.POST.get('email'),
                'password': make_password(request.POST.get('password')),
                'approved': True  # Auto-approve when added by admin
            }

            # Validate required fields
            required_fields = ['district', 'location', 'pincode', 'contact', 'email', 'password']
            if not all(data.get(field) for field in required_fields):
                messages.error(request, 'All fields are required.')
                return redirect('custom_admin:users')

            # Create police station
            PoliceStation.objects.create(**data)
            messages.success(request, f'Police station at {data["location"]} has been added successfully.')

        except Exception as e:
            messages.error(request, f'Error adding police station: {str(e)}')

        return redirect('custom_admin:users')

@method_decorator(require_http_methods(['POST']), name='dispatch')
class EditUserView(SuperUserRequiredMixin, View):
    def post(self, request):
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')

            if user_type == 'public':
                user = PublicUser.objects.get(id=user_id)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.phone = request.POST.get('phone', user.phone)
                user.save()
                messages.success(request, f'User {user.email} updated successfully.')

            elif user_type == 'police':
                station = PoliceStation.objects.get(id=user_id)
                station.district = request.POST.get('district', station.district)
                station.location = request.POST.get('location', station.location)
                station.contact = request.POST.get('contact', station.contact)
                station.pincode = request.POST.get('pincode', station.pincode)
                station.save()
                messages.success(request, f'Police station {station.location} updated successfully.')

        except (PublicUser.DoesNotExist, PoliceStation.DoesNotExist):
            messages.error(request, 'User or police station not found.')
        except Exception as e:
            messages.error(request, f'Error updating details: {str(e)}')

        return redirect('custom_admin:users')

class AdminLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('custom_admin:dashboard')
        return render(request, 'admin/login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
            return redirect('custom_admin:login')

class AdminLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')

class ComplaintListView(SuperUserRequiredMixin, TemplateView):
    template_name = 'admin/complaints.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get filter parameters
            status = self.request.GET.get('status')
            complaint_type = self.request.GET.get('type')
            district = self.request.GET.get('district')
            sort = self.request.GET.get('sort', '-registered_at')
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')

            # Base queryset
            complaints = Complaint.objects.select_related('user', 'police_station')

            # Apply filters
            if status:
                complaints = complaints.filter(status=status)
            if complaint_type:
                complaints = complaints.filter(complaint_type=complaint_type)
            if district and district != 'all':
                complaints = complaints.filter(police_station__district=district)
            if start_date:
                complaints = complaints.filter(registered_at__gte=start_date)
            if end_date:
                complaints = complaints.filter(registered_at__lte=end_date)

            # Apply sorting
            if sort == 'oldest':
                complaints = complaints.order_by('registered_at')
            elif sort == 'priority':
                complaints = complaints.order_by('-priority', '-registered_at')
            else:  # newest first (default)
                complaints = complaints.order_by('-registered_at')

            # Get unique districts for filter
            districts = PoliceStation.objects.values_list('district', flat=True).distinct()

            # Get unique complaint types for filter
            complaint_types = Complaint.objects.values_list('complaint_type', flat=True).distinct()

            context.update({
                'complaints': complaints,
                'districts': districts,
                'complaint_types': complaint_types,
                'current_filters': {
                    'status': status,
                    'type': complaint_type,
                    'district': district,
                    'sort': sort,
                    'start_date': start_date,
                    'end_date': end_date
                }
            })

        except Exception as e:
            messages.error(self.request, f'Error loading complaints: {str(e)}')
            context.update({
                'complaints': [],
                'districts': [],
                'complaint_types': [],
                'current_filters': {}
            })

        return context

class ComplaintDetailView(SuperUserRequiredMixin, TemplateView):
    template_name = 'admin/complaint_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            complaint_id = kwargs.get('complaint_id')
            complaint = Complaint.objects.select_related(
                'user',
                'police_station'
            ).prefetch_related(
                'complaintlog_set'
            ).get(id=complaint_id)

            # Get available police stations for assignment
            police_stations = PoliceStation.objects.filter(approved=True).order_by('district', 'location')

            context.update({
                'complaint': complaint,
                'police_stations': police_stations,
                'logs': complaint.complaintlog_set.all().order_by('-created_at')
            })

        except Complaint.DoesNotExist:
            messages.error(self.request, 'Complaint not found')
            return redirect('custom_admin:complaints')
        except Exception as e:
            messages.error(self.request, f'Error loading complaint details: {str(e)}')
            return redirect('custom_admin:complaints')

        return context

    def post(self, request, complaint_id):
        try:
            complaint = Complaint.objects.get(id=complaint_id)
            action = request.POST.get('action')

            if action == 'update_status':
                old_status = complaint.status
                new_status = request.POST.get('status')
                complaint.status = new_status
                complaint.save()

                # Log the status change
                ComplaintLog.objects.create(
                    complaint=complaint,
                    action='Status Update',
                    details=f'Status changed from {old_status} to {new_status}'
                )

                messages.success(request, 'Complaint status updated successfully')

            elif action == 'assign_station':
                station_id = request.POST.get('police_station')
                if station_id:
                    old_station = complaint.police_station
                    new_station = PoliceStation.objects.get(id=station_id)
                    complaint.police_station = new_station
                    complaint.save()

                    # Log the station assignment
                    ComplaintLog.objects.create(
                        complaint=complaint,
                        action='Station Assignment',
                        details=f'Assigned from {old_station.location if old_station else "None"} to {new_station.location}'
                    )

                    messages.success(request, 'Police station assigned successfully')

        except Exception as e:
            messages.error(request, f'Error updating complaint: {str(e)}')

        return redirect('custom_admin:complaint_detail', complaint_id=complaint_id)

class DonationHistoryView(SuperUserRequiredMixin, TemplateView):
    template_name = 'admin/donation_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get all donations
            donations = Donation.objects.all()
            
            # Apply filters
            status_filter = self.request.GET.get('status')
            if status_filter:
                donations = donations.filter(payment_status=status_filter)
                
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            min_amount = self.request.GET.get('min_amount')
            max_amount = self.request.GET.get('max_amount')
            search = self.request.GET.get('search')

            if start_date:
                donations = donations.filter(created_at__date__gte=start_date)
            if end_date:
                donations = donations.filter(created_at__date__lte=end_date)
            if min_amount:
                donations = donations.filter(amount__gte=min_amount)
            if max_amount:
                donations = donations.filter(amount__lte=max_amount)
            if search:
                donations = donations.filter(
                    Q(donor_name__icontains=search) |
                    Q(donor_email__icontains=search) |
                    Q(payment_id__icontains=search)
                )
            
            # Calculate statistics
            total_amount = donations.filter(payment_status='successful').aggregate(Sum('amount'))['amount__sum'] or 0
            successful_count = donations.filter(payment_status='successful').count()
            failed_count = donations.filter(payment_status='failed').count()
            total_count = donations.count()
            
            # Calculate average amount (only for successful donations)
            if successful_count > 0:
                average_amount = total_amount / successful_count
            else:
                average_amount = 0
            
            # Update context with statistics
            context.update({
                'total_amount': total_amount,
                'successful_count': successful_count,
                'failed_count': failed_count,
                'average_amount': average_amount,
                'total_count': total_count,
            })
            
            # Pagination
            paginator = Paginator(donations.order_by('-created_at'), 10)
            page = self.request.GET.get('page', 1)
            donations_page = paginator.get_page(page)
            
            context['donations'] = donations_page
            
        except Exception as e:
            print(f"Error in donation history: {str(e)}")
            context.update({
                'total_amount': 0,
                'successful_count': 0,
                'failed_count': 0,
                'average_amount': 0,
                'total_count': 0,
                'donations': [],
            })
        
        return context

class DonationDetailView(SuperUserRequiredMixin, View):
    def get(self, request, donation_id):
        try:
            donation = Donation.objects.get(id=donation_id)
            return JsonResponse({
                'created_at': donation.created_at.strftime('%Y-%m-%-d %H:%M:%S'),
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
