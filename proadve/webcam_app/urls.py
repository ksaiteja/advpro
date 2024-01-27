from django.urls import path
from .views import index, webcam_feed

urlpatterns = [
    path('', index, name='index'),
    path('webcam_feed/', webcam_feed, name='webcam_feed'),
]
