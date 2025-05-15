from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import PublicUser, PoliceStation, Complaint, FIR, Witness, FIREvidence, Donation

admin.site.register(PublicUser)
admin.site.register(PoliceStation)
admin.site.register(Complaint)
admin.site.register(FIR)
admin.site.register(Witness)
admin.site.register(FIREvidence)
admin.site.register(Donation)