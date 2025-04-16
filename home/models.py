from django.db import models

# Create your models here.
from django.db import models

class AttendanceRecord(models.Model):
    name = models.CharField(max_length=100)
    check_in_time = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    person_image = models.ImageField(upload_to='attendance_images/')
    working_time = models.DateTimeField(auto_now_add=True)
    seleping_time = models.DateTimeField(auto_now_add=True)
    activity_image = models.ImageField(upload_to='activity_images/')
    activity_type = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.name} - {self.check_in_time}"


class KnownFace(models.Model):
    name = models.CharField(max_length=100)        
    image = models.ImageField(upload_to='known_faces/')
    area_name = models.CharField(max_length=100)     
    area_x1 = models.IntegerField()
    area_y1 = models.IntegerField()
    area_x2 = models.IntegerField()
    area_y2 = models.IntegerField()

    def area_tuple(self):
        return (self.area_x1, self.area_y1, self.area_x2, self.area_y2)
