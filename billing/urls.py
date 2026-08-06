from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardSummaryView, CustomerViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('', include(router.urls)),
]
