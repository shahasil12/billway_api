from rest_framework import serializers
from .models import Customer, Product, Invoice, InvoiceItem, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

    def validate_email(self, value):
        if value:
            # Check for uniqueness, excluding the current instance if it's an update
            qs = Customer.objects.filter(email=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A customer with this email already exists.")
        return value

    def validate_phone(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 characters long.")
        return value

class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Invoice
        fields = ('id', 'customer', 'customer_name', 'total_amount', 'created_at')
