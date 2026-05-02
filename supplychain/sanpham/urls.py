from django.urls import path
from .views import danh_muc, san_pham

app_name = 'sanpham'

urlpatterns = [
    path('danhmuc/', danh_muc.danhmuc, name='danhmuc'),
    path('sanpham/', san_pham.sanpham, name='sanpham'),
]

