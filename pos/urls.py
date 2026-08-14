from django.urls import path
from .views import CurrentSessionView, OpenSessionView, CloseSessionView, POSCheckoutView, POSCashMovementView

urlpatterns = [
    path('sessions/current/', CurrentSessionView.as_view(), name='current_session'),
    path('sessions/open/', OpenSessionView.as_view(), name='open_session'),
    path('sessions/<uuid:pk>/close/', CloseSessionView.as_view(), name='close_session'),
    path('sessions/current/cash_movement/', POSCashMovementView.as_view(), name='cash_movement'),
    path('checkout/', POSCheckoutView.as_view(), name='pos_checkout'),
]
