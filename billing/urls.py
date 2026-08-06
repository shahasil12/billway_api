from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardSummaryView, CustomerViewSet, CategoryViewSet, ProductViewSet, InvoiceViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('', include(router.urls)),
]
