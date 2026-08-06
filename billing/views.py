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
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from rest_framework.decorators import action
from .serializers import CustomerSerializer, CategorySerializer, ProductSerializer, InvoiceReadSerializer, InvoiceCreateSerializer
from .models import Category, Customer, Invoice, Product
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import io

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'status', 'payment_method']
    search_fields = ['customer__name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InvoiceCreateSerializer
        return InvoiceReadSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        template_path = 'billing/invoice_pdf.html'
        context = {'invoice': invoice}
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        pisa_status = pisa.CreatePDF(
            html, dest=response
        )
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

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
