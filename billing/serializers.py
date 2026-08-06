from rest_framework import serializers
from .models import Customer, Product, Invoice, InvoiceItem, Category, Payment, BusinessSettings

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

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category.name', read_only=True, allow_null=True)

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'product_name', 'product_category', 'quantity', 'unit_price', 'tax_percentage', 'tax_amount', 'line_total']
        read_only_fields = ['unit_price', 'tax_percentage', 'tax_amount', 'line_total']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class BusinessSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = '__all__'

class InvoiceReadSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'

class InvoiceCreateItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceCreateItemSerializer(many=True, write_only=True)

    class Meta:
        model = Invoice
        fields = ['customer', 'discount_percentage', 'payment_method', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        discount_percentage = validated_data.get('discount_percentage', 0.00)
        
        # We will calculate totals
        subtotal = 0
        tax_total = 0

        # Calculate everything
        calculated_items = []
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Stock check
            if product.stock < quantity:
                raise serializers.ValidationError(f"Not enough stock for {product.name}. Available: {product.stock}")

            unit_price = product.price
            tax_perc = product.tax_percentage
            
            # Line subtotal before discount
            line_subtotal = unit_price * quantity
            subtotal += line_subtotal
            
            # Apply discount to this line's subtotal to calculate tax correctly
            discounted_line_subtotal = line_subtotal * (1 - discount_percentage / 100)
            
            # Calculate tax on the discounted amount
            tax_amount = discounted_line_subtotal * (tax_perc / 100)
            tax_total += tax_amount
            
            line_total = discounted_line_subtotal + tax_amount
            
            calculated_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'tax_percentage': tax_perc,
                'tax_amount': tax_amount,
                'line_total': line_total
            })

        discount_amount = subtotal * (discount_percentage / 100)
        grand_total = subtotal - discount_amount + tax_total

        # Create Invoice
        invoice = Invoice.objects.create(
            customer=validated_data['customer'],
            payment_method=validated_data.get('payment_method', 'CASH'),
            discount_percentage=discount_percentage,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_total=tax_total,
            grand_total=grand_total,
            status='PAID' if validated_data.get('payment_method') != 'OTHER' else 'UNPAID' # simple logic
        )

        # Create Items & Deduct Stock
        for ci in calculated_items:
            InvoiceItem.objects.create(
                invoice=invoice,
                product=ci['product'],
                quantity=ci['quantity'],
                unit_price=ci['unit_price'],
                tax_percentage=ci['tax_percentage'],
                tax_amount=ci['tax_amount'],
                line_total=ci['line_total']
            )
            # Deduct stock
            product = ci['product']
            product.stock -= ci['quantity']
            product.save()

        return invoice

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
