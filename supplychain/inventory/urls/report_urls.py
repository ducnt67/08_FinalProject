from django.urls import path

from inventory.views.report_views import baocao

urlpatterns = [
    path("baocao/", baocao, name="baocao"),
]

