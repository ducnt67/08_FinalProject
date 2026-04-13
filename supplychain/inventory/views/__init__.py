from .auth_views import login_view
from .dashboard_views import tongquan
from .product_views import sanpham
from .category_views import danhmuc
from .stock_views import tonkho, nhapkho, trahang, xuatkho, kiemke
from .supplier_views import ncc
from .order_views import dathang
from .report_views import baocao

__all__ = [
    "login_view",
    "tongquan",
    "sanpham",
    "danhmuc",
    "tonkho",
    "nhapkho",
    "trahang",
    "xuatkho",
    "kiemke",
    "ncc",
    "dathang",
    "baocao",
]