import uuid
from django.db import models
from django.conf import settings

class POSSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='pos_sessions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pos_sessions')
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_difference = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} - {self.user.username} ({self.status})"

class POSCashMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('IN', 'Cash In'),
        ('OUT', 'Cash Out'),
    ]

    pos_session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='cash_movements')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} {self.amount} for Session {self.pos_session.id}"
