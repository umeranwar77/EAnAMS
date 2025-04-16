from django.http import StreamingHttpResponse
from django.views.decorators import gzip
from .detection_utils import gen_frames  
from django.shortcuts import render, redirect
from .face_form import KnownFaceForm
from .models import KnownFace
import cv2


def home(request):
    return render(request, 'home.html')

def known_face(request):
    if request.method == 'POST':
        form = KnownFaceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')  
    else:
        form = KnownFaceForm()
    return render(request, 'known_face.html', {'form': form})



@gzip.gzip_page
def stream_view(request):
    return StreamingHttpResponse(gen_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')
   
import base64
from django.core.files.base import ContentFile

def save_image_with_area(request):
    if request.method == "POST":
        image_data = request.POST['image_data']
        format, imgstr = image_data.split(';base64,') 
        ext = format.split('/')[-1]
        image_file = ContentFile(base64.b64decode(imgstr), name=f"{request.POST['name']}.{ext}")
        
        known = KnownFace(
            name=request.POST['name'],
            image=image_file,
            area_name=request.POST['area_name'],
            area_x1=request.POST['area_x1'],
            area_y1=request.POST['area_y1'],
            area_x2=request.POST['area_x2'],
            area_y2=request.POST['area_y2'],
        )
        known.save()
        return redirect('home')  
