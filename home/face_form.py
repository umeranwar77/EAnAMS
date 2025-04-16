# forms.py
from django import forms
from .models import KnownFace

class KnownFaceForm(forms.ModelForm):
    class Meta:
        model = KnownFace
        fields = ['name', 'image', 'area_x1', 'area_y1', 'area_x2', 'area_y2']
