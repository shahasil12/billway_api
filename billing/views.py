from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from .models import Invoice, Customer, Product
from .serializers import InvoiceSerializer

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # Today's invoices
        todays_invoices = Invoice.objects.filter(created_at__date=today)
        
        # Metrics
        todays_sales = todays_invoices.aggregate(Sum('grand_total'))['grand_total__sum'] or 0.00
        todays_invoice_count = todays_invoices.count()
        total_customers = Customer.objects.count()
        total_products = Product.objects.count()
        total_invoices = Invoice.objects.count()
        
        # Recent Invoices
        recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]
        recent_invoices_data = InvoiceReadSerializer(recent_invoices, many=True).data
        
        return Response({
            'todays_sales': float(todays_sales),
            'todays_invoice_count': todays_invoice_count,
            'total_customers': total_customers,
            'total_products': total_products,
            'total_invoices': total_invoices,
            'recent_invoices': recent_invoices_data
        })
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from rest_framework.decorators import action
from .serializers import CustomerSerializer, CategorySerializer, ProductSerializer, InvoiceReadSerializer, InvoiceCreateSerializer, PaymentSerializer
from .models import Category, Customer, Invoice, Product, Payment
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response
import io

class IsManagerOrAdminOrReadOnly(BasePermission):
    """
    Authenticated users can read (GET, HEAD, OPTIONS).
    Manager/Admin users can do everything.
    Cashiers can also create.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'POST' and request.user.role == 'CASHIER':
            return True
        return request.user.role in ['ADMIN', 'MANAGER']

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.role in ['ADMIN', 'MANAGER']


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManagerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'status', 'payment_method']
    search_fields = ['customer__name']

    def get_queryset(self):
        if hasattr(self.request.user, 'company') and self.request.user.company:
            return Invoice.objects.filter(company=self.request.user.company).order_by('-created_at')
        return Invoice.objects.none()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InvoiceCreateSerializer
        return InvoiceReadSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        template_path = 'billing/invoice_pdf.html'
        settings = invoice.company
        
        context = {
            'invoice': invoice,
            'settings': settings,
        }
        
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

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice', 'payment_method']

    def get_queryset(self):
        if hasattr(self.request.user, 'company') and self.request.user.company:
            return Payment.objects.filter(invoice__company=self.request.user.company).order_by('-payment_date')
        return Payment.objects.none()

from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
        if hasattr(request.user, 'company') and request.user.company:
            invoices = Invoice.objects.filter(
                company=request.user.company,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
        else:
            invoices = Invoice.objects.none()
        
        # Summary
        total_sales = invoices.aggregate(Sum('grand_total'))['grand_total__sum'] or 0.00
        total_collected = invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0.00
        total_pending = float(total_sales) - float(total_collected)
        
        # Sales Trend
        trend = invoices.annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('grand_total')).order_by('date')
        trend_data = [{'date': t['date'].strftime('%Y-%m-%d'), 'total': float(t['total'])} for t in trend]
        
        # Top Products
        from .models import InvoiceItem
        items = InvoiceItem.objects.filter(invoice__in=invoices)
        top_products = items.values('product__name').annotate(quantity_sold=Sum('quantity'), revenue=Sum('line_total')).order_by('-revenue')[:5]
        top_products_data = [{'product_name': p['product__name'], 'quantity_sold': p['quantity_sold'], 'revenue': float(p['revenue'])} for p in top_products]
        
        # Recent Invoices
        recent_invoices = invoices.select_related('customer').order_by('-created_at')[:5]
        recent_invoices_data = InvoiceReadSerializer(recent_invoices, many=True).data

        return Response({
            'summary': {
                'total_sales': float(total_sales),
                'total_collected': float(total_collected),
                'total_pending': total_pending,
                'invoice_count': invoices.count()
            },
            'sales_trend': trend_data,
            'top_products': top_products_data,
            'recent_invoices': recent_invoices_data
        })



class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'barcode', 'description']

    def get_queryset(self):
        if hasattr(self.request.user, 'company') and self.request.user.company:
            return Product.objects.filter(company=self.request.user.company).order_by('-created_at')
        return Product.objects.none()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete product because it is part of an invoice."},
                status=400
            )

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        if hasattr(self.request.user, 'company') and self.request.user.company:
            return Category.objects.filter(company=self.request.user.company).order_by('-created_at')
        return Category.objects.none()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete category because there are products associated with it."},
                status=400
            )

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']

    def get_queryset(self):
        if hasattr(self.request.user, 'company') and self.request.user.company:
            return Customer.objects.filter(company=self.request.user.company).order_by('-created_at')
        return Customer.objects.none()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete customer because they have active invoices."},
                status=400
            )
