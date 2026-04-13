from django.urls import path, include

app_name = 'inventory'

urlpatterns = [
    path('', include('inventory.urls.auth_urls')),
    path('dashboard/', include('inventory.urls.dashboard_urls')),
    path('categories/', include('inventory.urls.category_urls')),
    path('products/', include('inventory.urls.product_urls')),
    path('orders/', include('inventory.urls.order_urls')),
    path('reports/', include('inventory.urls.report_urls')),
    path('stocks/', include('inventory.urls.stock_urls')),
    path('suppliers/', include('inventory.urls.supplier_urls')),
]