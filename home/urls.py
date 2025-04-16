from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('video/', views.stream_view, name='video-stream'),
    path('known_face/', views.known_face, name='known_face'),
    path('save-image/', views.save_image_with_area, name='save_image_with_area'),
]