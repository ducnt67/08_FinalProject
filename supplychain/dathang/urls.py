from django.urls import path
from .views import order_views

app_name = 'dathang'

urlpatterns = [
    path('dathang/', order_views.dathang, name='dathang'),
]
