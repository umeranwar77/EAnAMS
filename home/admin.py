from django.contrib import admin
from .models import AttendanceRecord, KnownFace

# Register your models here.
admin.site.register(AttendanceRecord)
admin.site.register(KnownFace)