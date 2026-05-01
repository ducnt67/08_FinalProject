from django.urls import path
from .views import stock_views, report_views

app_name = 'khohang'

urlpatterns = [
    path('tonkho/', stock_views.tonkho, name='tonkho'),
    path('nhapkho/', stock_views.nhapkho, name='nhapkho'),
    path('trahang/', stock_views.trahang, name='trahang'),
    path('xuatkho/', stock_views.xuatkho, name='xuatkho'),
    path('kiemke/', stock_views.kiemke, name='kiemke'),
    path('vitri/', stock_views.vitri_list, name='vitri_list'),
    path('baocao/', report_views.baocao, name='baocao'),
    path('auto-create-order/', stock_views.auto_create_order, name='auto_create_order'),
]
