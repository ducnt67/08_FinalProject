from django.urls import path

from inventory.views.category_views import danhmuc

urlpatterns = [
    path("danhmuc/", danhmuc, name="danhmuc"),
]

