from django.urls import path

from inventory.views.dashboard_views import tongquan

urlpatterns = [
    path("tongquan/", tongquan, name="tongquan"),
]

