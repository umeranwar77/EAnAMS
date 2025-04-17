from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('video/', views.stream_view, name='video-stream'),
    path('known_face/', views.known_face, name='known_face'),
    path('save-image/', views.save_image_with_area, name='save_image_with_area'),



    path('select/<int:image_id>/', views.select_keypoints, name='select_keypoints'),
    path('save-area/', views.save_area, name='save_area'),
    path('assign-person/', views.assign_person, name='assign_person'),
    path('upload-image/', views.upload_image, name='upload_image'),




    # path('camera/', views.camera_view, name='camera_view'),
    # # path('video_feed/', views.video_feed, name='video_feed'),
    # path('save_capture/', views.save_capture, name='save_capture')
]