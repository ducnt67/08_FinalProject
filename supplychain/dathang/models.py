from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

# 6. Đơn đặt hàng
class DonDatHang(models.Model):
    maDatHang = models.CharField(max_length=50, primary_key=True)
    ngayDatHang = models.DateTimeField(auto_now_add=True)
    nhaCungCap = models.ForeignKey('nhacungcap.NhaCungCap', on_delete=models.RESTRICT)
    trangThai = models.IntegerField()
    ghiChu = models.TextField(null=True, blank=True)
    nguoiLap = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'inventory_dondathang'
        constraints = [
            models.CheckConstraint(
                check=Q(trangThai__gte=0),
                name='ddh_trangThai_gte_0_new'
            ),
        ]


class DonDatHang_CT(models.Model):
    donDatHang = models.ForeignKey(DonDatHang, on_delete=models.CASCADE, related_name='dondathang_ct_set')
    sanPham = models.ForeignKey('sanpham.SanPham', on_delete=models.RESTRICT)
    soluongDat = models.IntegerField(validators=[MinValueValidator(1)])
    giaNhap = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    thanhTien = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory_dondathang_ct'
        constraints = [
            models.UniqueConstraint(
                fields=['donDatHang', 'sanPham'],
                name='ddhct_unique_donDatHang_sanPham_new'
            ),
            models.CheckConstraint(
                check=Q(soluongDat__gt=0),
                name='ddhct_soluongDat_gt_0_new'
            ),
            models.CheckConstraint(
                check=Q(giaNhap__gte=0),
                name='ddhct_giaNhap_gte_0_new'
            ),
            models.CheckConstraint(
                check=Q(thanhTien__gte=0),
                name='ddhct_thanhTien_gte_0_new'
            ),
        ]

    def clean(self):
        if self.soluongDat is not None and self.giaNhap is not None and self.thanhTien is not None:
            if self.thanhTien != self.soluongDat * self.giaNhap:
                raise ValidationError("thanhTien phải bằng soluongDat * giaNhap.")
