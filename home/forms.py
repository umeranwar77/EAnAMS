from django import forms
from .models import Image, Person

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']

# class AreaForm(forms.ModelForm):
#     class Meta:
#         model = Area
#         fields = ['area_name', 'x1', 'y1', 'x2', 'y2']

class PersonAssignForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['name', 'assigned_area']
