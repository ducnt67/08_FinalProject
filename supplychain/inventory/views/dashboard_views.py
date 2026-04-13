from django.db.models import F
from django.shortcuts import render
from django.utils import timezone

from inventory.models import DanhMuc, DonDatHang, KiemKe, NhaCungCap, NhapKho, SanPham, TonKho, XuatKho

def tongquan(request):
    total_products = SanPham.objects.count()
    total_categories = DanhMuc.objects.count()
    total_suppliers = NhaCungCap.objects.count()
    
    # Sản phẩm sắp hết (<= tồn kho tối thiểu)
    low_stock_products = TonKho.objects.filter(soluongTon__lte=F('sanPham__tonKhoToiThieu')).count()
    
    # Phiếu nhập tháng này
    now = timezone.now()
    inbound_records = NhapKho.objects.filter(ngayNhap__month=now.month, ngayNhap__year=now.year)
    
    # Đơn hàng chờ duyệt (trangThai = 0: Chờ xác nhận)
    orders = DonDatHang.objects.filter(trangThai=0)
    
    # Lấy các hoạt động gần đây từ Nhập kho, Xuất kho, Kiểm kê
    recent_inbound = NhapKho.objects.all().order_by('-ngayNhap')[:5]
    recent_outbound = XuatKho.objects.all().order_by('-ngayXuat')[:5]
    recent_check = KiemKe.objects.all().order_by('-ngayKiem')[:5]
    
    recent_activities = []
    
    for item in recent_inbound:
        recent_activities.append({
            'ma_phieu': item.maPhieuNhap,
            'loai_phieu': 'Nhập kho',
            'type': 'nhapkho',
            'icon': 'fa-file-import',
            'color': '#10b981',
            'ngay_tao': item.ngayNhap.strftime('%d/%m/%Y %H:%M'),
            'nguoi_thuc_hien': 'Admin',
            'trang_thai': 'Hoàn thành' if item.trangthaiNhap == 1 else 'Đang xử lý',
            'badge_class': 'badge-ok' if item.trangthaiNhap == 1 else 'badge-warn',
            'timestamp': item.ngayNhap,
            'link': '/inventory/nhapkho/'
        })
        
    for item in recent_outbound:
        recent_activities.append({
            'ma_phieu': item.maPhieuXuat,
            'loai_phieu': 'Xuất kho',
            'type': 'xuatkho',
            'icon': 'fa-file-export',
            'color': '#3b82f6',
            'ngay_tao': item.ngayXuat.strftime('%d/%m/%Y %H:%M'),
            'nguoi_thuc_hien': 'Admin',
            'trang_thai': 'Hoàn thành' if item.trangThai == 1 else 'Nháp',
            'badge_class': 'badge-ok' if item.trangThai == 1 else 'badge-warn',
            'timestamp': item.ngayXuat,
            'link': '/inventory/xuatkho/'
        })
        
    for item in recent_check:
        recent_activities.append({
            'ma_phieu': item.maKiemKe,
            'loai_phieu': 'Kiểm kê',
            'type': 'kiemke',
            'icon': 'fa-clipboard-check',
            'color': '#f59e0b',
            'ngay_tao': item.ngayKiem.strftime('%d/%m/%Y %H:%M'),
            'nguoi_thuc_hien': item.nguoiKiem,
            'trang_thai': 'Đã cân bằng' if item.trangThai == 1 else 'Đang kiểm',
            'badge_class': 'badge-ok' if item.trangThai == 1 else 'badge-warn',
            'timestamp': item.ngayKiem,
            'link': '/inventory/kiemke/'
        })
        
    # Sắp xếp tất cả hoạt động theo thời gian mới nhất
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]
    
    return render(request, 'inventory/dashboard/dashboard.html', {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'low_stock_products': low_stock_products,
        'inbound_records': inbound_records,
        'orders': orders,
        'recent_activities': recent_activities,
    })
