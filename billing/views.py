from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from .models import Invoice, Customer, Product
from .serializers import InvoiceSerializer

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Today's invoices
        todays_invoices = Invoice.objects.filter(created_at__date=today)
        
        # Metrics
        todays_sales = todays_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
        todays_invoice_count = todays_invoices.count()
        total_customers = Customer.objects.count()
        total_products = Product.objects.count()
        
        # Recent Invoices
        recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]
        recent_invoices_data = InvoiceSerializer(recent_invoices, many=True).data
        
        return Response({
            'todays_sales': float(todays_sales),
            'todays_invoice_count': todays_invoice_count,
            'total_customers': total_customers,
            'total_products': total_products,
            'recent_invoices': recent_invoices_data
        })

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError
from .serializers import CustomerSerializer, CategorySerializer, ProductSerializer
from .models import Category, Customer, Invoice, Product

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'barcode', 'description']

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete product because it is part of an invoice."},
                status=400
            )

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete category because there are products associated with it."},
                status=400
            )

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete customer because they have active invoices."},
                status=400
            )
