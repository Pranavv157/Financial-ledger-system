from django.urls import path
from .views import TransferAPIView

urlpatterns = [
    path("transfer/", TransferAPIView.as_view(),name="transfer"),
]