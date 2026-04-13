from django.urls import path

from inventory.views.product_views import sanpham

urlpatterns = [
    path("sanpham/", sanpham, name="sanpham"),
]

