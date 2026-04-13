from django.urls import include, path

app_name = "inventory"

urlpatterns = [
    path("", include("inventory.urls.auth_urls")),
    path("", include("inventory.urls.dashboard_urls")),
    path("", include("inventory.urls.product_urls")),
    path("", include("inventory.urls.category_urls")),
    path("", include("inventory.urls.stock_urls")),
    path("", include("inventory.urls.supplier_urls")),
    path("", include("inventory.urls.order_urls")),
    path("", include("inventory.urls.report_urls")),
]

