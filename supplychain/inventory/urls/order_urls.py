from django.urls import path

from inventory.views.order_views import dathang

urlpatterns = [
    path("dathang/", dathang, name="dathang"),
]

