from rest_framework import serializers
from .models import POSSession, POSCashMovement
from billing.models import Invoice, InvoiceItem, Payment, Product, Customer

class POSSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSession
        fields = '__all__'
        read_only_fields = ('id', 'company', 'user', 'opened_at', 'closed_at', 'status', 'expected_cash', 'cash_difference')

class POSSessionCloseSerializer(serializers.Serializer):
    closing_cash = serializers.DecimalField(max_digits=12, decimal_places=2)

class POSCheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=0.00)

class POSCheckoutSerializer(serializers.Serializer):
    items = POSCheckoutItemSerializer(many=True)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_CHOICES, default='CASH')

class POSCashMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSCashMovement
        fields = '__all__'
        read_only_fields = ('id', 'pos_session', 'created_at')
