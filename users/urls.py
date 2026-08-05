from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .views import CurrentUserView, LogoutView, ChangePasswordView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
]
