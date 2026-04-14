from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q, F


# 1. Danh mục sản phẩm
class DanhMuc(models.Model):
    maDanhMuc = models.CharField(max_length=50, primary_key=True)
    tenDanhMuc = models.CharField(max_length=255)
    maDanhMucCha = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    trangThai = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(trangThai__in=[0, 1]),
                name='dm_trangThai_valid'
            ),
            models.CheckConstraint(
                condition=~Q(maDanhMuc=F('maDanhMucCha')),
                name='dm_not_self_parent'
            ),
        ]

    def clean(self):
        if self.maDanhMucCha_id and self.maDanhMucCha_id == self.maDanhMuc:
            raise ValidationError("maDanhMucCha không được trùng với maDanhMuc.")

    def __str__(self):
        return self.tenDanhMuc


# 2. Nhà cung cấp
class NhaCungCap(models.Model):
    maNCC = models.CharField(max_length=50, primary_key=True)
    tenNCC = models.CharField(max_length=255)
    soDienThoai = models.CharField(max_length=15)
    email = models.EmailField()
    diaChi = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['soDienThoai'], name='ncc_unique_soDienThoai'),
            models.UniqueConstraint(fields=['email'], name='ncc_unique_email'),
        ]

    def __str__(self):
        return self.tenNCC


class SanPham(models.Model):
    maSP = models.CharField(max_length=50, primary_key=True)
    danhMuc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    tenSP = models.CharField(max_length=255)
    donViTinh = models.CharField(max_length=50)
    giaBan = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    tonKhoToiThieu = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    trangThai = models.IntegerField(default=1)
    moTa = models.TextField(null=True, blank=True)
    anhSP = models.ImageField(upload_to='products/', null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(giaBan__gte=0),
                name='sp_giaBan_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(tonKhoToiThieu__gte=0),
                name='sp_tonKhoToiThieu_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(trangThai__in=[0, 1]),
                name='sp_trangThai_valid'
            ),
        ]

    def clean(self):
        errors = {}

        # Chuẩn hóa dữ liệu text
        if self.tenSP:
            self.tenSP = self.tenSP.strip()
        if self.donViTinh:
            self.donViTinh = self.donViTinh.strip()
        if self.moTa:
            self.moTa = self.moTa.strip()

        # 1. Tên sản phẩm không được rỗng
        if not self.tenSP:
            errors['tenSP'] = 'Tên sản phẩm không được để trống.'

        # 2. Tên sản phẩm nên có độ dài tối thiểu
        elif len(self.tenSP) < 2:
            errors['tenSP'] = 'Tên sản phẩm phải có ít nhất 2 ký tự.'

        # 3. Đơn vị tính không được rỗng
        if not self.donViTinh:
            errors['donViTinh'] = 'Đơn vị tính không được để trống.'

        # 4. Danh mục bắt buộc phải có
        if not self.danhMuc_id:
            errors['danhMuc'] = 'Sản phẩm phải thuộc một danh mục.'

        # 5. Nhà cung cấp bắt buộc phải có
        if not self.nhaCungCap_id:
            errors['nhaCungCap'] = 'Sản phẩm phải có nhà cung cấp.'

        # 6. Giá bán không được âm
        if self.giaBan is not None and self.giaBan < 0:
            errors['giaBan'] = 'Giá bán không được nhỏ hơn 0.'

        # 7. Nếu sản phẩm đang hoạt động thì giá bán nên > 0
        if self.trangThai == 1 and self.giaBan is not None and self.giaBan <= 0:
            errors['giaBan'] = 'Sản phẩm đang hoạt động thì giá bán phải lớn hơn 0.'

        # 8. Tồn kho tối thiểu không được âm
        if self.tonKhoToiThieu is not None and self.tonKhoToiThieu < 0:
            errors['tonKhoToiThieu'] = 'Tồn kho tối thiểu không được nhỏ hơn 0.'

        # 9. Kiểm tra ảnh sản phẩm (nếu có)
        if self.anhSP:
            allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
            image_type = getattr(self.anhSP, 'content_type', None)
            if image_type and image_type not in allowed_types:
                errors['anhSP'] = 'Ảnh sản phẩm chỉ chấp nhận JPG, PNG hoặc WEBP.'

            max_size = 5 * 1024 * 1024
            if self.anhSP.size and self.anhSP.size > max_size:
                errors['anhSP'] = 'Ảnh sản phẩm không được vượt quá 5MB.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()  # gọi clean() trước khi lưu
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tenSP


# 4. Chi tiết sách
class ChiTiet_Sach(models.Model):
    sanPham = models.OneToOneField(SanPham, on_delete=models.CASCADE, primary_key=True)
    tacGia = models.CharField(max_length=255)
    nhaXuatBan = models.CharField(max_length=255)
    namXuatBan = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(namXuatBan__gte=0),
                name='cts_namXuatBan_gte_0'
            ),
        ]


# 5. Tồn kho
class TonKho(models.Model):
    sanPham = models.OneToOneField(SanPham, on_delete=models.CASCADE, primary_key=True, related_name='tonkho')
    soluongTon = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    # 0: An toàn, 1: Sắp hết (<= tối thiểu), 2: Hết hàng (=0)
    trangthaiCanhBao = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(soluongTon__gte=0),
                name='tk_soLuongTon_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(trangthaiCanhBao__in=[0, 1, 2]),
                name='tk_trangthaiCanhBao_valid'
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


# 6. Đơn đặt hàng
class DonDatHang(models.Model):
    maDatHang = models.CharField(max_length=50, primary_key=True)
    ngayDatHang = models.DateTimeField(auto_now_add=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    trangThai = models.IntegerField()
    ghiChu = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(trangThai__gte=0),
                name='ddh_trangThai_gte_0'
            ),
        ]


class DonDatHang_CT(models.Model):
    donDatHang = models.ForeignKey(DonDatHang, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongDat = models.IntegerField(validators=[MinValueValidator(1)])
    giaNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['donDatHang', 'sanPham'],
                name='ddhct_unique_donDatHang_sanPham'
            ),
            models.CheckConstraint(
                condition=Q(soluongDat__gt=0),
                name='ddhct_soluongDat_gt_0'
            ),
            models.CheckConstraint(
                condition=Q(giaNhap__gte=0),
                name='ddhct_giaNhap_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(thanhTien__gte=0),
                name='ddhct_thanhTien_gte_0'
            ),
        ]

    def clean(self):
        if self.soluongDat is not None and self.giaNhap is not None and self.thanhTien is not None:
            if self.thanhTien != self.soluongDat * self.giaNhap:
                raise ValidationError("thanhTien phải bằng soluongDat * giaNhap.")


# 7. Nhập kho
class NhapKho(models.Model):
    maPhieuNhap = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    ngayNhap = models.DateTimeField()
    trangthaiNhap = models.IntegerField(default=0, choices=[(0, 'Phiếu tạm'), (1, 'Đã hoàn thành'), (-1, 'Đã hủy')])
    ghichu = models.TextField(null=True, blank=True)
    donDatHang = models.ForeignKey(DonDatHang, on_delete=models.SET_NULL, null=True)
    tongtienNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(trangthaiNhap__gte=-1),
                name='nk_trangthaiNhap_gte_minus_1'
            ),
            models.CheckConstraint(
                condition=Q(tongtienNhap__gte=0),
                name='nk_tongtienNhap_gte_0'
            ),
        ]


class PhieuNhap_CT(models.Model):
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongDat = models.IntegerField(validators=[MinValueValidator(1)])
    dongiaNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    soluongThucNhan = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phieuNhap', 'sanPham'],
                name='pnct_unique_phieuNhap_sanPham'
            ),
            models.CheckConstraint(
                condition=Q(soluongDat__gt=0),
                name='pnct_soluongDat_gt_0'
            ),
            models.CheckConstraint(
                condition=Q(dongiaNhap__gte=0),
                name='pnct_dongiaNhap_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(thanhTien__gte=0),
                name='pnct_thanhTien_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(soluongThucNhan__gte=0),
                name='pnct_soluongThucNhan_gte_0'
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
        constraints = [
            models.CheckConstraint(
                condition=Q(trangThai__gte=-1),
                name='xk_trangThai_gte_minus_1'
            ),
        ]


class PhieuXuat_CT(models.Model):
    phieuXuat = models.ForeignKey(XuatKho, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongXuat = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phieuXuat', 'sanPham'],
                name='pxct_unique_phieuXuat_sanPham'
            ),
            models.CheckConstraint(
                condition=Q(soluongXuat__gt=0),
                name='pxct_soluongXuat_gt_0'
            ),
        ]


# 9. Kiểm kê
class KiemKe(models.Model):
    maKiemKe = models.CharField(max_length=50, primary_key=True)
    ngayKiem = models.DateTimeField()
    nguoiKiem = models.CharField(max_length=100)
    trangThai = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(trangThai__gte=0),
                name='kk_trangThai_gte_0'
            ),
        ]


class KiemKe_CT(models.Model):
    kiemKe = models.ForeignKey(KiemKe, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    slTonKho = models.IntegerField(validators=[MinValueValidator(0)])
    slThucTe = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['kiemKe', 'sanPham'],
                name='kkct_unique_kiemKe_sanPham'
            ),
            models.CheckConstraint(
                condition=Q(slTonKho__gte=0),
                name='kkct_slTonKho_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(slThucTe__gte=0),
                name='kkct_slThucTe_gte_0'
            ),
        ]


# 10. Trả hàng NCC
class TraHangNCC(models.Model):
    maPhieuTra = models.CharField(max_length=50, primary_key=True)
    nhaCungCap = models.ForeignKey(NhaCungCap, on_delete=models.CASCADE)
    ngayTra = models.DateTimeField()
    phieuNhap = models.ForeignKey(NhapKho, on_delete=models.SET_NULL, null=True)
    trangThai = models.IntegerField(default=0, choices=[(0, 'Phiếu tạm'), (1, 'Đã trả hàng'), (-1, 'Đã hủy')])
    tongtienTra = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(trangThai__gte=-1),
                name='thncc_trangThai_gte_minus_1'
            ),
            models.CheckConstraint(
                condition=Q(tongtienTra__gte=0),
                name='thncc_tongtienTra_gte_0'
            ),
        ]


class TraHangNCC_CT(models.Model):
    phieuTra = models.ForeignKey(TraHangNCC, on_delete=models.CASCADE)
    sanPham = models.ForeignKey(SanPham, on_delete=models.CASCADE)
    soluongTra = models.IntegerField(validators=[MinValueValidator(1)])
    dongiaTra = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    lydoTra = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phieuTra', 'sanPham'],
                name='thnccct_unique_phieuTra_sanPham'
            ),
            models.CheckConstraint(
                condition=Q(soluongTra__gt=0),
                name='thnccct_soluongTra_gt_0'
            ),
            models.CheckConstraint(
                condition=Q(dongiaTra__gte=0),
                name='thnccct_dongiaTra_gte_0'
            ),
            models.CheckConstraint(
                condition=Q(thanhTien__gte=0),
                name='thnccct_thanhTien_gte_0'
            ),
        ]

    def clean(self):
        if self.soluongTra is not None and self.dongiaTra is not None and self.thanhTien is not None:
            if self.thanhTien != self.soluongTra * self.dongiaTra:
                raise ValidationError("thanhTien phải bằng soluongTra * dongiaTra.")