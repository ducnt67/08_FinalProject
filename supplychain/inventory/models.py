from django.db import models

# Create your models here.
from django.db import models

# 1. Danh mục sản phẩm
class DanhMuc(models.Model):
    maDanhMuc = models.CharField(max_length=50, primary_key=True)
    tenDanhMuc = models.CharField(max_length=255)
    maDanhMucCha = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    trangThai = models.IntegerField(default=1)

    def __str__(self):
        return self.tenDanhMuc

# 2. Nhà cung cấp
class NhaCungCap(models.Model):
    maNCC = models.CharField(max_length=50, primary_key=True)
    tenNCC = models.CharField(max_length=255)
    soDienThoai = models.CharField(max_length=15)
    email = models.EmailField()
    diaChi = models.TextField()

    def __str__(self):
        return self.tenNCC

# 3. Sản phẩm
class SanPham(models.Model):
    maSP = models.CharField(max_length=50, primary_key=True)
    danhMuc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    tenSP = models.CharField(max_length=255)
    donViTinh = models.CharField(max_length=50)
    giaBan = models.DecimalField(max_digits=15, decimal_places=2)
    tonKhoToiThieu = models.IntegerField(default=0)
    trangThai = models.IntegerField(default=1)
    moTa = models.TextField(null=True, blank=True)
    anhSP = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return self.tenSP

# 4. Chi tiết sách (Nếu là hệ thống quản lý sách)
class ChiTiet_Sach(models.Model):
    sanPham = models.OneToOneField(SanPham, on_delete=models.CASCADE, primary_key=True)
    tacGia = models.CharField(max_length=255)
    nhaXuatBan = models.CharField(max_length=255)
    namXuatBan = models.IntegerField()

# 5. Tồn kho
class TonKho(models.Model):
    sanPham = models.OneToOneField(SanPham, on_delete=models.CASCADE, primary_key=True, related_name='tonkho')
    soluongTon = models.IntegerField(default=0)
    # 0: An toàn, 1: Sắp hết (<= tối thiểu), 2: Hết hàng (=0)
    trangthaiCanhBao = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.soluongTon == 0:
            self.trangthaiCanhBao = 2
        elif self.soluongTon <= self.sanPham.tonKhoToiThieu:
            self.trangthaiCanhBao = 1
        else:
            self.trangthaiCanhBao = 0
        super().save(*args, **kwargs)

# 6. Đơn đặt hàng (Đặt từ Nhà cung cấp)
class DonDatHang(models.Model):
    maDatHang = models.CharField(max_length=50, primary_key=True)
    ngayDatHang = models.DateTimeField(auto_now_add=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    trangThai = models.IntegerField()
    ghiChu = models.TextField(null=True, blank=True)

class DonDatHang_CT(models.Model):
    donDatHang = models.ForeignKey(DonDatHang, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongDat = models.IntegerField()
    giaNhap = models.DecimalField(max_digits=15, decimal_places=2)
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2)

# 7. Nhập kho
class NhapKho(models.Model):
    maPhieuNhap = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    ngayNhap = models.DateTimeField()
    trangthaiNhap = models.IntegerField()
    ghichu = models.TextField(null=True, blank=True)
    donDatHang = models.ForeignKey(DonDatHang, on_delete=models.SET_NULL, null=True)
    tongtienNhap = models.DecimalField(max_digits=15, decimal_places=2)

class PhieuNhap_CT(models.Model):
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongDat = models.IntegerField()
    dongiaNhap = models.DecimalField(max_digits=15, decimal_places=2)
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2)
    soluongThucNhan = models.IntegerField()

# 8. Xuất kho
class XuatKho(models.Model):
    maPhieuXuat = models.CharField(max_length=50, primary_key=True)
    ngayXuat = models.DateTimeField()
    noiXuat = models.CharField(max_length=255)
    trangThai = models.IntegerField()

class PhieuXuat_CT(models.Model):
    phieuXuat = models.ForeignKey(XuatKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongXuat = models.IntegerField()

# 9. Kiểm kê
class KiemKe(models.Model):
    maKiemKe = models.CharField(max_length=50, primary_key=True)
    ngayKiem = models.DateTimeField()
    nguoiKiem = models.CharField(max_length=100)
    trangThai = models.IntegerField()

class KiemKe_CT(models.Model):
    kiemKe = models.ForeignKey(KiemKe, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    slTonKho = models.IntegerField()
    slThucTe = models.IntegerField()

# 10. Trả hàng NCC
class TraHangNCC(models.Model):
    maPhieuTra = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    ngayTra = models.DateTimeField()
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.SET_NULL, null=True)
    tongtienTra = models.DecimalField(max_digits=15, decimal_places=2)

class TraHangNCC_CT(models.Model):
    phieuTra = models.ForeignKey(TraHangNCC, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongTra = models.IntegerField()
    dongiaTra = models.DecimalField(max_digits=15, decimal_places=2)
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2)
    lydoTra = models.TextField()