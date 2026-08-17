from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from rest_framework.routers import DefaultRouter
from .views import CurrentUserView, LogoutView, ChangePasswordView, UserViewSet, RegisterView, CustomTokenObtainPairView
from . import views

router = DefaultRouter()
router.register(r'manage', UserViewSet, basename='manage-users')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('company/', views.CompanyView.as_view(), name='company'),
    path('', include(router.urls)),
]
