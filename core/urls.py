from django.urls import path
from .views import GenerateUploadUrlView, PingView

urlpatterns = [
    path('ping/', PingView.as_view(), name='ping'),
    path('generate-upload-url/', GenerateUploadUrlView.as_view(), name='generate-upload-url'),
]
