from rest_framework import serializers
from .models import Customer, Product, Invoice, InvoiceItem, Category, Payment, StockMovement

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['company']

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def validate_name(self, value):
        qs = Product.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if hasattr(self.context.get('request'), 'user') and hasattr(self.context['request'].user, 'company'):
            qs = qs.filter(company=self.context['request'].user.company)
        if qs.exists():
            raise serializers.ValidationError("A product with this name already exists.")
        return value

    def validate_barcode(self, value):
        if value:
            qs = Product.objects.filter(barcode__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if hasattr(self.context.get('request'), 'user') and hasattr(self.context['request'].user, 'company'):
                qs = qs.filter(company=self.context['request'].user.company)
            if qs.exists():
                raise serializers.ValidationError("A product with this barcode already exists.")
        return value

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['company']

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
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, write_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'reference', 'discount_percentage', 'payment_method', 'amount_paid', 'items']
        read_only_fields = ['id']

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
            if product.track_stock and product.stock < quantity:
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

        # Auto-generate reference if not provided
        reference = validated_data.get('reference')
        
        # Create Invoice
        invoice = Invoice.objects.create(
            customer=validated_data.get('customer'),
            company=validated_data.get('company'),
            payment_method=validated_data.get('payment_method', 'CASH'),
            discount_percentage=discount_percentage,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_total=tax_total,
            grand_total=grand_total,
            reference=reference,
            status='UNPAID'
        )
        
        if not reference:
            company = invoice.company
            prefix = company.invoice_prefix if company else "INV-"
            invoice.reference = f"{prefix}{invoice.id}"
            invoice.save(update_fields=['reference'])

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
            if product.track_stock:
                product.stock -= ci['quantity']
                product.save()
                StockMovement.objects.create(
                    product=product,
                    movement_type='SALE',
                    quantity=-ci['quantity'],
                    reference=invoice.reference
                )

        # Handle amount_paid
        amount_paid = validated_data.get('amount_paid', 0)
        if amount_paid > 0:
            Payment.objects.create(
                invoice=invoice,
                amount=amount_paid,
                payment_method=validated_data.get('payment_method', 'CASH'),
                notes='Initial payment at checkout'
            )
            # The signal will automatically update the invoice amount_paid and status

        # Refresh from db since signals might have modified it
        invoice.refresh_from_db()
        return invoice

    def to_representation(self, instance):
        return InvoiceReadSerializer(instance, context=self.context).data

class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Invoice
        fields = ('id', 'customer', 'customer_name', 'total_amount', 'created_at')
