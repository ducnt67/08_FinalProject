from django.urls import path

from inventory.views.stock_views import kiemke, nhapkho, tonkho, trahang, xuatkho

urlpatterns = [
    path("tonkho/", tonkho, name="tonkho"),
    path("nhapkho/", nhapkho, name="nhapkho"),
    path("trahang/", trahang, name="trahang"),
    path("xuatkho/", xuatkho, name="xuatkho"),
    path("kiemke/", kiemke, name="kiemke"),
]

