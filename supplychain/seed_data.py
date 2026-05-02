import os
import django
import sys
import random
from datetime import datetime, timedelta

# Thiết lập môi trường Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'supplychain.settings')
django.setup()

from nhacungcap.models import NhaCungCap
from sanpham.models import DanhMuc, SanPham
from khohang.models import ViTriKho, TonKho, TonKhoChiTiet, XuatKho, PhieuXuat_CT, KiemKe, KiemKe_CT

def seed():
    print("Seeding 50+ items of sample data...")

    # 1. Nhà cung cấp
    nccs = []
    for i in range(1, 6):
        ncc, _ = NhaCungCap.objects.get_or_create(
            maNCC=f'NCC{i:03d}',
            defaults={
                'tenNCC': f'Nhà cung cấp {i}', 
                'soDienThoai': f'09000000{i:02d}', 
                'email': f'ncc{i}@example.com', 
                'diaChi': f'Địa chỉ {i}'
            }
        )
        nccs.append(ncc)

    # 2. Danh mục
    dms = []
    names = ['Sách Giáo Khoa', 'Sách Tham Khảo', 'Dụng cụ học tập', 'Văn phòng phẩm', 'Sách Ngoại Ngữ']
    for i, name in enumerate(names, 1):
        dm, _ = DanhMuc.objects.get_or_create(maDanhMuc=f'DM{i:03d}', defaults={'tenDanhMuc': name})
        dms.append(dm)

    # 3. Vị trí kho (Tạo 10 vị trí)
    vts = []
    for i in range(1, 11):
        vt, _ = ViTriKho.objects.get_or_create(
            maViTri=f'V{i:02d}', 
            defaults={'khuVuc': f'Khu {"A" if i<=5 else "B"}', 'keKho': f'Kệ {i}', 'oChua': f'Ô {i}'}
        )
        vts.append(vt)

    # 4. Sản phẩm (Tạo 50 sản phẩm)
    products = []
    for i in range(1, 51):
        dm = random.choice(dms)
        ncc = random.choice(nccs)
        sp, _ = SanPham.objects.get_or_create(
            maSP=f'SP{i:03d}',
            defaults={
                'tenSP': f'Sản phẩm mẫu số {i}',
                'danhMuc': dm,
                'nhaCungCap': ncc,
                'donViTinh': random.choice(['Cuốn', 'Cái', 'Bộ', 'Ram']),
                'giaBan': random.randint(10, 500) * 1000,
                'tonKhoToiThieu': random.randint(10, 50),
                'trangThai': 1
            }
        )
        products.append(sp)
        
        # Tạo Tồn kho tổng hợp
        total_qty = random.randint(100, 1000)
        TonKho.objects.get_or_create(sanPham=sp, defaults={'soluongTon': total_qty})
        
        # Phân bổ vào 1-3 vị trí kho
        assigned_vts = random.sample(vts, k=random.randint(1, 3))
        remaining_qty = total_qty
        for j, vt in enumerate(assigned_vts):
            if j == len(assigned_vts) - 1:
                qty = remaining_qty
            else:
                qty = random.randint(1, remaining_qty)
            TonKhoChiTiet.objects.get_or_create(sanPham=sp, viTri=vt, defaults={'soluong': qty})
            remaining_qty -= qty

    # 5. Dữ liệu mẫu cho Xuất kho (10 phiếu)
    for i in range(1, 11):
        px, _ = XuatKho.objects.get_or_create(
            maPhieuXuat=f'PX{i:03d}',
            defaults={
                'ngayXuat': datetime.now() - timedelta(days=random.randint(0, 30)),
                'noiXuat': f'Địa điểm nhận hàng {i}',
                'trangThai': random.choice([0, 1, -1])
            }
        )
        # Mỗi phiếu xuất 2-5 sản phẩm
        px_products = random.sample(products, k=random.randint(2, 5))
        for sp in px_products:
            # Lấy 1 vị trí có hàng của sản phẩm này
            tk_ct = TonKhoChiTiet.objects.filter(sanPham=sp).first()
            if tk_ct:
                PhieuXuat_CT.objects.get_or_create(
                    phieuXuat=px, 
                    sanPham=sp, 
                    viTri=tk_ct.viTri, 
                    defaults={'soluongXuat': random.randint(1, 20)}
                )

    # 6. Dữ liệu mẫu cho Kiểm kê (10 phiếu)
    for i in range(1, 11):
        kk, _ = KiemKe.objects.get_or_create(
            maKiemKe=f'KK{i:03d}',
            defaults={
                'ngayKiem': datetime.now() - timedelta(days=random.randint(0, 30)),
                'nguoiKiem': f'Nhân viên {random.choice(["A", "B", "C"])}',
                'trangThai': random.choice([0, 1])
            }
        )
        # Mỗi phiếu kiểm 3-6 sản phẩm
        kk_products = random.sample(products, k=random.randint(3, 6))
        for sp in kk_products:
            tk_ct = TonKhoChiTiet.objects.filter(sanPham=sp).first()
            if tk_ct:
                actual = tk_ct.soluong + random.randint(-5, 5)
                KiemKe_CT.objects.get_or_create(
                    kiemKe=kk, 
                    sanPham=sp, 
                    viTri=tk_ct.viTri, 
                    defaults={'slTonKho': tk_ct.soluong, 'slThucTe': max(0, actual)}
                )

    print("Seed data successful with 50 products!")

if __name__ == '__main__':
    seed()
