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
        db_table = 'inventory_danhmuc'
        # constraints = [
        #     models.CheckConstraint(
        #         check=Q(trangThai__in=[0, 1]),
        #         name='dm_trangThai_valid_new'
        #     ),
        #     models.CheckConstraint(
        #         check=~Q(maDanhMuc=F('maDanhMucCha')),
        #         name='dm_not_self_parent_new'
        #     ),
        # ]

    def clean(self):
        if self.maDanhMucCha_id and self.maDanhMucCha_id == self.maDanhMuc:
            raise ValidationError("maDanhMucCha không được trùng với maDanhMuc.")

    def __str__(self):
        return self.tenDanhMuc


class SanPham(models.Model):
    maSP = models.CharField(max_length=50, primary_key=True)
    danhMuc = models.ForeignKey(DanhMuc, on_delete=models.RESTRICT)
    nhaCungCap = models.ForeignKey('nhacungcap.NhaCungCap', on_delete=models.RESTRICT)
    tenSP = models.CharField(max_length=255)
    donViTinh = models.CharField(max_length=50)
    giaBan = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    tonKhoToiThieu = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    trangThai = models.IntegerField(default=1)
    moTa = models.TextField(null=True, blank=True)
    anhSP = models.ImageField(upload_to='products/', null=True, blank=True)

    class Meta:
        db_table = 'inventory_sanpham'
        # constraints = [
        #     models.CheckConstraint(
        #         check=Q(giaBan__gte=0),
        #         name='sp_giaBan_gte_0_new'
        #     ),
        #     models.CheckConstraint(
        #         check=Q(tonKhoToiThieu__gte=0),
        #         name='sp_tonKhoToiThieu_gte_0_new'
        #     ),
        #     models.CheckConstraint(
        #         check=Q(trangThai__in=[0, 1]),
        #         name='sp_trangThai_valid_new'
        #     ),
        # ]

    def clean(self):
        errors = {}
        if self.tenSP: self.tenSP = self.tenSP.strip()
        if self.donViTinh: self.donViTinh = self.donViTinh.strip()
        if self.moTa: self.moTa = self.moTa.strip()

        if not self.tenSP: errors['tenSP'] = 'Tên sản phẩm không được để trống.'
        elif len(self.tenSP) < 2: errors['tenSP'] = 'Tên sản phẩm phải có ít nhất 2 ký tự.'
        if not self.donViTinh: errors['donViTinh'] = 'Đơn vị tính không được để trống.'
        if not self.danhMuc_id: errors['danhMuc'] = 'Sản phẩm phải thuộc một danh mục.'
        if not self.nhaCungCap_id: errors['nhaCungCap'] = 'Sản phẩm phải có nhà cung cấp.'
        if self.giaBan is not None and self.giaBan < 0: errors['giaBan'] = 'Giá bán không được nhỏ hơn 0.'
        if self.trangThai == 1 and self.giaBan is not None and self.giaBan <= 0:
            errors['giaBan'] = 'Sản phẩm đang hoạt động thì giá bán phải lớn hơn 0.'
        if self.tonKhoToiThieu is not None and self.tonKhoToiThieu < 0:
            errors['tonKhoToiThieu'] = 'Tồn kho tối thiểu không được nhỏ hơn 0.'

        if self.anhSP:
            allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
            image_type = getattr(self.anhSP, 'content_type', None)
            if image_type and image_type not in allowed_types:
                errors['anhSP'] = 'Ảnh sản phẩm chỉ chấp nhận JPG, PNG hoặc WEBP.'
            max_size = 5 * 1024 * 1024
            if self.anhSP.size and self.anhSP.size > max_size:
                errors['anhSP'] = 'Ảnh sản phẩm không được vượt quá 5MB.'

        if errors: raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
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
        db_table = 'inventory_chitiet_sach'
        # constraints = [
        #     models.CheckConstraint(
        #         check=Q(namXuatBan__gte=0),
        #         name='cts_namXuatBan_gte_0_new'
        #     ),
        # ]
