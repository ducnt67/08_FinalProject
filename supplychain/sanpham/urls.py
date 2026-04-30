from django.urls import path
from .views import category_views, product_views

app_name = 'sanpham'

urlpatterns = [
    path('danhmuc/', category_views.danhmuc, name='danhmuc'),
    path('sanpham/', product_views.sanpham, name='sanpham'),
]
