from django.urls import path
from .views import auth_views, dashboard_views

app_name = 'hethong'

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('tongquan/', dashboard_views.tongquan, name='tongquan'),
]
