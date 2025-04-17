from django.contrib import admin
from .models import AttendanceRecord, KnownFace,Area,Person,Image

# Register your models here.
admin.site.register(AttendanceRecord)
admin.site.register(KnownFace)
admin.site.register(Area)
admin.site.register(Person)
admin.site.register(Image)