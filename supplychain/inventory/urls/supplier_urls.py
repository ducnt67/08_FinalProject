from django.urls import path

from inventory.views.supplier_views import ncc

urlpatterns = [
    path("ncc/", ncc, name="ncc"),
]

