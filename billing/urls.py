from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardSummaryView, CustomerViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('', include(router.urls)),
]
