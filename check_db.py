import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billway_api.settings")
django.setup()

from billing.models import Invoice, Payment
from django.utils import timezone

today = timezone.now().date()
todays_invoices = Invoice.objects.filter(created_at__date=today)
print(f"Total invoices today: {todays_invoices.count()}")
for inv in todays_invoices:
    print(f"Invoice {inv.id}: status={inv.status}, amount_paid={inv.amount_paid}, grand_total={inv.grand_total}, payment_method={inv.payment_method}, customer={inv.customer_id}")
    
payments = Payment.objects.filter(payment_date__date=today)
print(f"Total payments today: {payments.count()}")
for p in payments:
    print(f"Payment {p.id}: amount={p.amount}, method={p.payment_method}")
