from django.urls import path
from .views import don_hang

app_name = 'dathang'

urlpatterns = [
    path('dathang/', don_hang.dathang, name='dathang'),
]

