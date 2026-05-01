from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

# --- NEW WMS MODELS ---

class ViTriKho(models.Model):
    maViTri = models.CharField(max_length=50, primary_key=True) # VD: A1-1-01
    khuVuc = models.CharField(max_length=100) # Khu A, Khu B
    keKho = models.CharField(max_length=100) # Kệ A1, Kệ A2
    oChua = models.CharField(max_length=100) # Ô số 3
    ghiChu = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'inventory_vitrikho'
        verbose_name = "Vị trí kho"

    def __str__(self):
        return self.maViTri

class LoHang(models.Model):
    maLo = models.CharField(max_length=50, primary_key=True)
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT, related_name='lohangs')
    ngaySanXuat = models.DateField(null=True, blank=True)
    hanSuDung = models.DateField(null=True, blank=True)
    ngayNhapVao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_lohang'
        verbose_name = "Lô hàng"

    def __str__(self):
        return f"{self.maLo} ({self.sanPham.tenSanPham})"

class TonKhoChiTiet(models.Model):
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    viTri = models.ForeignKey(ViTriKho, on_delete=models.RESTRICT)
    soluong = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_tonkho_chitiet'
        unique_together = ('sanPham', 'viTri')

# --- EXISTING MODELS (UPDATED) ---

# 5. Tồn kho (Summary)
class TonKho(models.Model):
    sanPham = models.OneToOneField('sanpham.SanPham', on_delete=models.RESTRICT, primary_key=True, related_name='tonkho')
    soluongTon = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    trangthaiCanhBao = models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory_tonkho'
        constraints = [
            models.CheckConstraint(
                check=Q(soluongTon__gte=0),
                name='tk_soLuongTon_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(trangthaiCanhBao__in=[0, 1, 2]),
                name='tk_trangthaiCanhBao_valid_new'
            ),
        ]

    def save(self, *args, **kwargs):
        if self.soluongTon == 0:
            self.trangthaiCanhBao = 2
        elif self.soluongTon <= self.sanPham.tonKhoToiThieu:
            self.trangthaiCanhBao = 1
        else:
            self.trangthaiCanhBao = 0
        super().save(*args, **kwargs)


# 7. Nhập kho
class NhapKho(models.Model):
    maPhieuNhap = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey('nhacungcap.NhaCungCap', on_delete=models.RESTRICT)
    ngayNhap = models.DateTimeField()
    trangthaiNhap = models.IntegerField(default=0, choices=[(0, 'Phiếu tạm'), (1, 'Đã hoàn thành'), (-1, 'Đã hủy')])
    ghichu = models.TextField(null=True, blank=True)
    donDatHang = models.ForeignKey('dathang.DonDatHang', on_delete=models.SET_NULL, null=True)
    nguoiLap = models.CharField(max_length=100, null=True, blank=True)
    tongtienNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_nhapkho'
        constraints = [
            models.CheckConstraint(
                check=Q(trangthaiNhap__gte=-1),
                name='nk_trangthaiNhap_gte_minus_1_new'
            ),
            models.CheckConstraint(
                check=Q(tongtienNhap__gte=0),
                name='nk_tongtienNhap_gte_0_new'
            ),
        ]


class PhieuNhap_CT(models.Model):
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    viTri = models.ForeignKey(ViTriKho, on_delete=models.SET_NULL, null=True, blank=True)
    soluongDat = models.IntegerField(validators=[MinValueValidator(1)])
    dongiaNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    soluongThucNhan = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_phieunhap_ct'
        constraints = [
            models.CheckConstraint(
                check=Q(soluongDat__gt=0),
                name='pnct_soluongDat_gt_0_new'
            ),
            models.CheckConstraint(
                check=Q(dongiaNhap__gte=0),
                name='pnct_dongiaNhap_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(thanhTien__gte=0),
                name='pnct_thanhTien_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(soluongThucNhan__gte=0),
                name='pnct_soluongThucNhan_gte_0_new'
            ),
        ]

    def clean(self):
        if self.soluongThucNhan is not None and self.soluongDat is not None:
            if self.soluongThucNhan > self.soluongDat:
                raise ValidationError("soluongThucNhan không được lớn hơn soluongDat.")
        if self.soluongThucNhan is not None and self.dongiaNhap is not None and self.thanhTien is not None:
            if self.thanhTien != self.soluongThucNhan * self.dongiaNhap:
                raise ValidationError("thanhTien phải bằng soluongThucNhan * dongiaNhap.")


# 8. Xuất kho
class XuatKho(models.Model):
    maPhieuXuat = models.CharField(max_length=50, primary_key=True)
    ngayXuat = models.DateTimeField()
    noiXuat = models.CharField(max_length=255)
    trangThai = models.IntegerField(default=0, choices=[(0, 'Nháp'), (1, 'Hoàn thành'), (-1, 'Đã hủy')])

    class Meta:
        db_table = 'inventory_xuatkho'
        constraints = [
            models.CheckConstraint(
                check=Q(trangThai__gte=-1),
                name='xk_trangThai_gte_minus_1_new'
            ),
        ]


class PhieuXuat_CT(models.Model):
    phieuXuat = models.ForeignKey(XuatKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    viTri = models.ForeignKey(ViTriKho, on_delete=models.SET_NULL, null=True, blank=True)
    soluongXuat = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'inventory_phieuxuat_ct'
        constraints = [
            models.CheckConstraint(
                check=Q(soluongXuat__gt=0),
                name='pxct_soluongXuat_gt_0_new'
            ),
        ]


# 9. Kiểm kê
class KiemKe(models.Model):
    maKiemKe = models.CharField(max_length=50, primary_key=True)
    ngayKiem = models.DateTimeField()
    nguoiKiem = models.CharField(max_length=100)
    trangThai = models.IntegerField()

    class Meta:
        db_table = 'inventory_kiemke'
        constraints = [
            models.CheckConstraint(
                check=Q(trangThai__gte=0),
                name='kk_trangThai_gte_0_new'
            ),
        ]


class KiemKe_CT(models.Model):
    kiemKe = models.ForeignKey(KiemKe, on_delete=models.CASCADE)
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    viTri = models.ForeignKey(ViTriKho, on_delete=models.SET_NULL, null=True, blank=True)
    slTonKho = models.IntegerField(validators=[MinValueValidator(0)])
    slThucTe = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_kiemke_ct'
        constraints = [
            models.CheckConstraint(
                check=Q(slTonKho__gte=0),
                name='kkct_slTonKho_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(slThucTe__gte=0),
                name='kkct_slThucTe_gte_0_new'
            ),
        ]


# 10. Trả hàng NCC
class TraHangNCC(models.Model):
    maPhieuTra = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey('nhacungcap.NhaCungCap', on_delete=models.RESTRICT)
    ngayTra = models.DateTimeField()
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.SET_NULL, null=True)
    trangThai = models.IntegerField(default=0, choices=[(0, 'Phiếu tạm'), (1, 'Đã trả hàng'), (-1, 'Đã hủy')])
    tongtienTra = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_trahangncc'
        constraints = [
            models.CheckConstraint(
                check=Q(trangThai__gte=-1),
                name='thncc_trangThai_gte_minus_1_new'
            ),
            models.CheckConstraint(
                check=Q(tongtienTra__gte=0),
                name='thncc_tongtienTra_gte_0_new'
            ),
        ]


class TraHangNCC_CT(models.Model):
    phieuTra = models.ForeignKey(TraHangNCC, on_delete=models.CASCADE)
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    soluongTra = models.IntegerField(validators=[MinValueValidator(1)])
    dongiaTra = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    lydoTra = models.TextField()

    class Meta:
        db_table = 'inventory_trahangncc_ct'
        constraints = [
            models.UniqueConstraint(
                fields=['phieuTra', 'sanPham'],
                name='thnccct_unique_phieuTra_sanPham_new'
            ),
            models.CheckConstraint(
                check=Q(soluongTra__gt=0),
                name='thnccct_soluongTra_gt_0_new'
            ),
            models.CheckConstraint(
                check=Q(dongiaTra__gte=0),
                name='thnccct_dongiaTra_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(thanhTien__gte=0),
                name='thnccct_thanhTien_gte_0_new'
            ),
        ]

    def clean(self):
        if self.soluongTra is not None and self.dongiaTra is not None and self.thanhTien is not None:
            if self.thanhTien != self.soluongTra * self.dongiaTra:
                raise ValidationError("thanhTien phải bằng soluongTra * dongiaTra.")
