from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum

from .models import POSSession
from .serializers import POSSessionSerializer, POSSessionCloseSerializer, POSCheckoutSerializer
from billing.models import Invoice, InvoiceItem, Payment, Product, Customer
from billing.serializers import InvoiceReadSerializer

class CurrentSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = POSSession.objects.filter(user=request.user, status='OPEN').first()
        if session:
            return Response(POSSessionSerializer(session).data)
        return Response({'detail': 'No active session found.'}, status=status.HTTP_404_NOT_FOUND)


class OpenSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active_session = POSSession.objects.filter(user=request.user, status='OPEN').exists()
        if active_session:
            return Response({'detail': 'You already have an open session.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = POSSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, status='OPEN')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CloseSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            session = POSSession.objects.get(pk=pk, user=request.user, status='OPEN')
        except POSSession.DoesNotExist:
            return Response({'detail': 'Active session not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = POSSessionCloseSerializer(data=request.data)
        if serializer.is_valid():
            closing_cash = serializer.validated_data['closing_cash']
            
            # Calculate expected cash: opening_cash + total CASH payments in this session
            cash_sales = Payment.objects.filter(
                invoice__pos_session=session, 
                payment_method='CASH'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expected_cash = session.opening_cash + cash_sales
            cash_difference = closing_cash - expected_cash

            session.closing_cash = closing_cash
            session.expected_cash = expected_cash
            session.cash_difference = cash_difference
            session.status = 'CLOSED'
            session.closed_at = timezone.now()
            session.save()

            return Response(POSSessionSerializer(session).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class POSCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        session = POSSession.objects.filter(user=request.user, status='OPEN').first()
        if not session:
            return Response({'detail': 'You must have an open session to checkout.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = POSCheckoutSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            customer = None
            if data.get('customer_id'):
                try:
                    customer = Customer.objects.get(id=data['customer_id'])
                except Customer.DoesNotExist:
                    return Response({'detail': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Create Invoice
            invoice = Invoice.objects.create(
                customer=customer,
                pos_session=session,
                subtotal=data['subtotal'],
                discount_percentage=data['discount_percentage'],
                discount_amount=data['discount_amount'],
                tax_total=data['tax_total'],
                grand_total=data['grand_total'],
                amount_paid=0, # Signal will update this when Payment is created
                status='UNPAID'
            )

            # Create Invoice Items
            for item_data in data['items']:
                product = Product.objects.get(id=item_data['product_id'])
                line_total = (item_data['unit_price'] * item_data['quantity']) + (
                    item_data['unit_price'] * item_data['quantity'] * item_data['tax_percentage'] / 100
                )
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    tax_percentage=item_data['tax_percentage'],
                    tax_amount=(item_data['unit_price'] * item_data['quantity'] * item_data['tax_percentage'] / 100),
                    line_total=line_total
                )
                
                # Deduct stock
                if product.stock >= item_data['quantity']:
                    product.stock -= item_data['quantity']
                    product.save()

            # Create Payment
            Payment.objects.create(
                invoice=invoice,
                amount=data['amount_paid'],
                payment_method=data['payment_method'],
                reference_number=f"POS-{session.id}"
            )
            
            # Re-fetch invoice to get updated amount_paid and status from signals
            invoice.refresh_from_db()
            
            return Response(InvoiceReadSerializer(invoice).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
