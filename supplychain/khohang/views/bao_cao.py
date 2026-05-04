from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from khohang.models import KiemKe, NhapKho, PhieuXuat_CT, TonKho, XuatKho


def baocao(request):
    # =====================================================
    # CẤU HÌNH TRẠNG THÁI HOÀN THÀNH
    # =====================================================
    NHAP_KHO_HOAN_THANH = 1
    XUAT_KHO_HOAN_THANH = 1

    KIEM_KE_HOAN_THANH = 1

    now = timezone.now()
    today = now.date()
    current_year = now.year
    current_month = now.month

    # =====================================================
    # LẤY THÁNG/NĂM ĐƯỢC CHỌN TỪ GIAO DIỆN
    # =====================================================
    try:
        selected_year = int(request.GET.get('year', current_year))
    except (TypeError, ValueError):
        selected_year = current_year

    try:
        selected_month = int(request.GET.get('month', current_month))
    except (TypeError, ValueError):
        selected_month = current_month

    if selected_month < 1 or selected_month > 12:
        selected_month = current_month

    # =====================================================
    # 1. KPI CARDS - SỐ LIỆU HIỆN TẠI
    # =====================================================

    inventory_items = TonKho.objects.select_related('sanPham').all()

    total_value = sum(
        Decimal(item.soluongTon) * item.sanPham.giaBan
        for item in inventory_items
    )

    inventory_value_tr = float(total_value) / 1_000_000

    low_stock_count = TonKho.objects.filter(
        soluongTon__lte=F('sanPham__tonKhoToiThieu'),
        soluongTon__gt=0
    ).count()

    today_nhap = NhapKho.objects.filter(
        ngayNhap__date=today,
        trangthaiNhap=NHAP_KHO_HOAN_THANH
    ).count()

    today_xuat = XuatKho.objects.filter(
        ngayXuat__date=today,
        trangThai=XUAT_KHO_HOAN_THANH
    ).count()

    today_kiemke = KiemKe.objects.filter(
        ngayKiem__date=today,
        trangThai=KIEM_KE_HOAN_THANH
    ).count()

    today_transactions = today_nhap + today_xuat + today_kiemke

    # =====================================================
    # 2. BIỂU ĐỒ XUẤT/NHẬP KHO THEO THÁNG
    # =====================================================
    monthly_imports = [0] * 12
    monthly_exports = [0] * 12

    nhap_by_month = (
        NhapKho.objects
        .filter(
            ngayNhap__year=selected_year,
            trangthaiNhap=NHAP_KHO_HOAN_THANH
        )
        .annotate(month=TruncMonth('ngayNhap'))
        .values('month')
        .annotate(total=Count('maPhieuNhap'))
        .order_by('month')
    )

    for item in nhap_by_month:
        if item['month']:
            monthly_imports[item['month'].month - 1] = item['total']

    xuat_by_month = (
        XuatKho.objects
        .filter(
            ngayXuat__year=selected_year,
            trangThai=XUAT_KHO_HOAN_THANH
        )
        .annotate(month=TruncMonth('ngayXuat'))
        .values('month')
        .annotate(total=Count('maPhieuXuat'))
        .order_by('month')
    )

    for item in xuat_by_month:
        if item['month']:
            monthly_exports[item['month'].month - 1] = item['total']

    # =====================================================
    # 3. TOP SẢN PHẨM XUẤT NHIỀU NHẤT
    # =====================================================
    top_items = (
        PhieuXuat_CT.objects
        .filter(
            phieuXuat__ngayXuat__year=selected_year,
            phieuXuat__ngayXuat__month=selected_month,
            phieuXuat__trangThai=XUAT_KHO_HOAN_THANH
        )
        .values('sanPham__tenSP')
        .annotate(total_qty=Sum('soluongXuat'))
        .order_by('-total_qty')[:5]
    )

    top_products_labels = [
        item['sanPham__tenSP']
        for item in top_items
        if item['sanPham__tenSP']
    ]

    top_products_data = [
        item['total_qty'] or 0
        for item in top_items
        if item['sanPham__tenSP']
    ]

    # =====================================================
    # 4. TÌNH TRẠNG TỒN KHO HIỆN TẠI
    # =====================================================
    status_normal = TonKho.objects.filter(
        soluongTon__gt=F('sanPham__tonKhoToiThieu')
    ).count()

    status_warning = TonKho.objects.filter(
        soluongTon__lte=F('sanPham__tonKhoToiThieu'),
        soluongTon__gt=0
    ).count()

    status_danger = TonKho.objects.filter(
        soluongTon=0
    ).count()

    inventory_status_data = [
        status_normal,
        status_warning,
        status_danger
    ]

    # =====================================================
    # 5. DOANH THU TẠM TÍNH THEO DANH MỤC
    # =====================================================
    revenue_expression = ExpressionWrapper(
        F('soluongXuat') * F('sanPham__giaBan'),
        output_field=DecimalField(max_digits=20, decimal_places=2)
    )

    revenue_by_cat = (
        PhieuXuat_CT.objects
        .filter(
            phieuXuat__ngayXuat__year=selected_year,
            phieuXuat__ngayXuat__month=selected_month,
            phieuXuat__trangThai=XUAT_KHO_HOAN_THANH
        )
        .values(
            'sanPham__danhMuc__maDanhMucCha__tenDanhMuc',
            'sanPham__danhMuc__tenDanhMuc'
        )
        .annotate(revenue=Sum(revenue_expression))
        .order_by('-revenue')
    )

    revenue_labels = []
    revenue_data = []

    for item in revenue_by_cat:
        parent_name = item.get('sanPham__danhMuc__maDanhMucCha__tenDanhMuc') or ''
        child_name = item.get('sanPham__danhMuc__tenDanhMuc') or ''
        revenue = item.get('revenue') or Decimal('0')

        if child_name:
            if parent_name:
                revenue_labels.append(f'{parent_name} / {child_name}')
            else:
                revenue_labels.append(child_name)

            revenue_data.append(float(revenue) / 1_000_000)

    # =====================================================
    # 6. DỮ LIỆU CHO BỘ LỌC
    # =====================================================
    available_months = [
        {'value': 1, 'label': 'Tháng 1'},
        {'value': 2, 'label': 'Tháng 2'},
        {'value': 3, 'label': 'Tháng 3'},
        {'value': 4, 'label': 'Tháng 4'},
        {'value': 5, 'label': 'Tháng 5'},
        {'value': 6, 'label': 'Tháng 6'},
        {'value': 7, 'label': 'Tháng 7'},
        {'value': 8, 'label': 'Tháng 8'},
        {'value': 9, 'label': 'Tháng 9'},
        {'value': 10, 'label': 'Tháng 10'},
        {'value': 11, 'label': 'Tháng 11'},
        {'value': 12, 'label': 'Tháng 12'},
    ]

    available_years = list(range(current_year, current_year - 5, -1))

    context = {
        'inventory_value': inventory_value_tr,
        'low_stock_count': low_stock_count,
        'today_transactions': today_transactions,
        'current_time': now.strftime('%H:%M, %d/%m/%Y'),

        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_months': available_months,
        'available_years': available_years,

        'monthly_imports': monthly_imports,
        'monthly_exports': monthly_exports,

        'top_products_labels': top_products_labels,
        'top_products_data': top_products_data,

        'inventory_status_data': inventory_status_data,

        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
    }

    return render(request, 'khohang/reports/bao_cao.html', context)
