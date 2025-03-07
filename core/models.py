from django.db import models
from django.core.validators import RegexValidator

# Public User model
class PublicUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    adhaar = models.CharField(max_length=12, unique=True)
    password = models.CharField(max_length=255)  # Password field to store the hashed password
    is_verified = models.BooleanField(default=False)  # Add a flag to indicate whether OTP is verified

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

