from django.urls import path
from .views import nha_cung_cap

app_name = 'nhacungcap'

urlpatterns = [
    path('ncc/', nha_cung_cap.ncc, name='ncc'),
]

