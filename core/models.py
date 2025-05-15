from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import os

# Public User model
class PublicUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    adhaar = models.CharField(max_length=12, unique=True)
    address = models.TextField(null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    password = models.CharField(max_length=255)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

# Police Station model
class PoliceStation(models.Model):
    district = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    contact = models.CharField(max_length=15)
    email = models.EmailField(unique=True)  # Added email field
    password = models.CharField(max_length=255)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.location}, {self.district}, {self.pincode}"

# Complaint model
class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ('Robbery', 'Robbery'),
        ('Assault', 'Assault'),
        ('Threats', 'Threats'),
        ('Burglary', 'Burglary'),
        ('Vandalism', 'Vandalism'),
        ('Fraud', 'Fraud'),
        ('Harassment', 'Harassment'),
        ('Theft', 'Theft'),
        ('Domestic Violence', 'Domestic Violence'),
        ('Sexual Assault', 'Sexual Assault'),
        ('Kidnapping', 'Kidnapping'),
        ('Stalking', 'Stalking'),
        ('Drunk Driving', 'Drunk Driving'),
        ('Hit and Run', 'Hit and Run'),
        ('Drug Offenses', 'Drug Offenses'),
        ('Public Intoxication', 'Public Intoxication'),
        ('Trespassing', 'Trespassing'),
        ('Hate Crimes', 'Hate Crimes'),
        ('Murder', 'Murder'),
        ('Arson', 'Arson'),
        ('Others', 'Others'),
    ]
    
    TIME_CHOICES = [
        ('Midnight', '12:00 AM - 12:59 AM'),
        ('Morning', '6:00 AM - 11:59 AM'),
        ('Noon', '12:00 PM - 12:59 PM'),
        ('Afternoon', '1:00 PM - 5:59 PM'),
        ('Evening', '6:00 PM - 8:59 PM'),
        ('Night', '9:00 PM - 11:59 PM'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Under Investigation', 'Under Investigation'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(PublicUser, on_delete=models.CASCADE)
    police_station = models.ForeignKey(PoliceStation, on_delete=models.CASCADE)
    complaint_type = models.CharField(max_length=50, choices=COMPLAINT_TYPES)
    incident_date = models.DateField()
    incident_time = models.CharField(max_length=20, choices=TIME_CHOICES)
    incident_location = models.TextField(default='Location not specified')
    description = models.TextField()
    evidence = models.FileField(upload_to='complaint_evidence/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    registered_at = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.complaint_type} - {self.user.first_name} - {self.registered_at.strftime('%Y-%m-%d')}"
    
    def filename(self):
        if self.evidence:
            return os.path.basename(self.evidence.name)
        return None

class FIR(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='fir')
    spot_location = models.CharField(max_length=255, null=True, blank=True)
    police_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FIR for Complaint #{self.complaint.id}"

class FIRDescription(models.Model):
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='additional_descriptions')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Description for FIR #{self.fir.id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']

class FIREvidence(models.Model):
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='additional_evidence')
    file = models.FileField(upload_to='fir_evidence/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence for FIR #{self.fir.id}"

class Witness(models.Model):
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='witnesses', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class ComplaintLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)  # To store who made the change

    def __str__(self):
        return f"{self.action} - {self.complaint} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class PasswordResetToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=6)  # OTP
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    user_type = models.CharField(max_length=20)  # 'public' or 'police'
    
    def is_valid(self):
        # Token expires after 10 minutes
        return not self.is_used and (timezone.now() - self.created_at).seconds < 600

class Donation(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed')
    )

    user = models.ForeignKey(PublicUser, on_delete=models.SET_NULL, null=True, blank=True)
    donor_name = models.CharField(max_length=255, null=True, blank=True)
    donor_email = models.EmailField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    order_id = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Donation {self.payment_id or self.order_id} - {self.amount} by {self.donor_name or 'Anonymous'}"

    class Meta:
        ordering = ['-created_at']