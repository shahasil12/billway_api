from django.urls import path
from .views import GenerateUploadUrlView

urlpatterns = [
    path('generate-upload-url/', GenerateUploadUrlView.as_view(), name='generate-upload-url'),
]
