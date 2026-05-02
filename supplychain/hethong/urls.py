from django.urls import path
from .views import xac_thuc, tong_quan

app_name = 'hethong'

urlpatterns = [
    path('dangnhap/', xac_thuc.login_view, name='login'),
    path('tongquan/', tong_quan.tongquan, name='tongquan'),
]

