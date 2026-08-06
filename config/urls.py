from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def create_temp_superuser(request):
    User = get_user_model()
    if not User.objects.filter(username='shahasil').exists():
        User.objects.create_superuser('shahasil', 'shahasil@example.com', 'admin')
        return JsonResponse({"status": "Created superuser shahasil with password admin"})
    
    # Just in case they need the password reset to admin
    user = User.objects.get(username='shahasil')
    user.set_password('admin')
    user.save()
    return JsonResponse({"status": "User shahasil already exists, reset password to admin"})

urlpatterns = [
    path('api/create-admin/', create_temp_superuser),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('billing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
