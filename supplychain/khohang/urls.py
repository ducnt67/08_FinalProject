from django.urls import path
from .views import nghiep_vu_kho, bao_cao

app_name = 'khohang'

urlpatterns = [
    path('tonkho/', nghiep_vu_kho.tonkho, name='tonkho'),
    path('nhapkho/', nghiep_vu_kho.nhapkho, name='nhapkho'),
    path('trahang/', nghiep_vu_kho.trahang, name='trahang'),
    path('xuatkho/', nghiep_vu_kho.xuatkho, name='xuatkho'),
    path('kiemke/', nghiep_vu_kho.kiemke, name='kiemke'),
    path('vitri/', nghiep_vu_kho.vitri_list, name='vitri_list'),
    path('baocao/', bao_cao.baocao, name='baocao'),
    path('auto-create-order/', nghiep_vu_kho.auto_create_order, name='auto_create_order'),
]

