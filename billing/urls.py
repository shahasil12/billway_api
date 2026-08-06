from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardSummaryView, CustomerViewSet, CategoryViewSet, ProductViewSet, InvoiceViewSet, PaymentViewSet, ReportView, BusinessSettingsView

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('settings/', BusinessSettingsView.as_view(), name='business_settings'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('reports/', ReportView.as_view(), name='reports'),
    path('', include(router.urls)),
]
