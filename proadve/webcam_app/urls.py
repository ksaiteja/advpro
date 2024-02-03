from django.urls import path
from webcam_app.views import webcam_feed,index,advertisement

urlpatterns = [
    path('', index, name='index'),
    path('webcam_feed/', webcam_feed, name='webcam_feed'),
    path('advertisement/', advertisement, name='advertisement'),
]
