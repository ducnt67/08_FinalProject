from django.urls import path
from inventory.views.auth_views import login_view

urlpatterns = [
    path('login/', login_view, name='login'),
]