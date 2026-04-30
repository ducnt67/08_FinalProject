from django.urls import path
from .views import supplier_views

app_name = 'nhacungcap'

urlpatterns = [
    path('ncc/', supplier_views.ncc, name='ncc'),
]
