from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from inventory.models import KiemKe, NhapKho, PhieuXuat_CT, TonKho, XuatKho

def baocao(request):
    # 1. KPI Cards
    # Giá trị tồn kho = sum(soluongTon * giaBan)
    inventory_items = TonKho.objects.select_related('sanPham').all()
    total_value = sum(item.soluongTon * item.sanPham.giaBan for item in inventory_items)
    inventory_value_tr = float(total_value) / 1_000_000  # Đổi sang triệu

    # Sản phẩm sắp hết (<= tồn kho tối thiểu)
    low_stock_count = TonKho.objects.filter(soluongTon__lte=F('sanPham__tonKhoToiThieu')).count()
    
    # Giao dịch hôm nay (Nhập + Xuất + Kiểm kê)
    today = timezone.now().date()
    today_nhap = NhapKho.objects.filter(ngayNhap__date=today).count()
    today_xuat = XuatKho.objects.filter(ngayXuat__date=today).count()
    today_kiemke = KiemKe.objects.filter(ngayKiem__date=today).count()
    today_transactions = today_nhap + today_xuat + today_kiemke
    
    # 2. Charts
    # Xuất nhập kho theo tháng (12 tháng trong năm hiện tại)
    current_year = timezone.now().year
    monthly_imports = [0] * 12
    monthly_exports = [0] * 12
    
    nhap_by_month = NhapKho.objects.filter(ngayNhap__year=current_year)\
        .annotate(month=TruncMonth('ngayNhap'))\
        .values('month')\
        .annotate(total=Count('maPhieuNhap'))\
        .order_by('month')
        
    for item in nhap_by_month:
        monthly_imports[item['month'].month - 1] = item['total']
        
    xuat_by_month = XuatKho.objects.filter(ngayXuat__year=current_year)\
        .annotate(month=TruncMonth('ngayXuat'))\
        .values('month')\
        .annotate(total=Count('maPhieuXuat'))\
        .order_by('month')
        
    for item in xuat_by_month:
        monthly_exports[item['month'].month - 1] = item['total']

    # Top sản phẩm bán chạy (dựa trên phiếu xuất tháng này)
    current_month = timezone.now().month
    top_items = PhieuXuat_CT.objects.filter(phieuXuat__ngayXuat__month=current_month)\
        .values('sanPham__tenSP')\
        .annotate(total_qty=Sum('soluongXuat'))\
        .order_by('-total_qty')[:5]
    
    top_products_labels = [item['sanPham__tenSP'] for item in top_items]
    top_products_data = [item['total_qty'] for item in top_items]

    # Tình trạng tồn kho (Bình thường, Sắp hết, Hết hàng)
    status_normal = TonKho.objects.filter(soluongTon__gt=F('sanPham__tonKhoToiThieu')).count()
    status_warning = TonKho.objects.filter(soluongTon__lte=F('sanPham__tonKhoToiThieu'), soluongTon__gt=0).count()
    status_danger = TonKho.objects.filter(soluongTon=0).count()
    inventory_status_data = [status_normal, status_warning, status_danger]

    # Doanh thu theo danh mục (dựa trên phiếu xuất)
    revenue_by_cat = PhieuXuat_CT.objects.filter(phieuXuat__ngayXuat__month=current_month)\
        .values('sanPham__danhMuc__tenDanhMuc')\
        .annotate(revenue=Sum(F('soluongXuat') * F('sanPham__giaBan')))\
        .order_by('-revenue')
        
    revenue_labels = [item['sanPham__danhMuc__tenDanhMuc'] for item in revenue_by_cat if item['sanPham__danhMuc__tenDanhMuc']]
    revenue_data = [float(item['revenue']) / 1_000_000 for item in revenue_by_cat if item['sanPham__danhMuc__tenDanhMuc']]

    context = {
        'inventory_value': inventory_value_tr,
        'low_stock_count': low_stock_count,
        'today_transactions': today_transactions,
        'current_time': timezone.now().strftime('%H:%M, %d/%m/%Y'),
        'monthly_imports': monthly_imports,
        'monthly_exports': monthly_exports,
        'top_products_labels': top_products_labels,
        'top_products_data': top_products_data,
        'inventory_status_data': inventory_status_data,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
    }
    return render(request, 'inventory/reports/report_dashboard.html', context)
