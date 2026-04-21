from django.urls import path
from .views import TransferAPIView, AccountBalanceAPIView, AccountTransactionsAPIView ,TransferStatusAPIView

urlpatterns = [
    path("transfers/", TransferAPIView.as_view(), name="transfer"),

    path(
        "accounts/<int:account_id>/balance/",
        AccountBalanceAPIView.as_view(),
        name="account-balance"
    ),

    path(
        "accounts/<int:account_id>/transactions/",
        AccountTransactionsAPIView.as_view(),
        name="account-transactions"
    ),
    path("transfers/<uuid:reference_id>/", TransferStatusAPIView.as_view())
]