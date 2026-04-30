from django.db import models

# 2. Nhà cung cấp
class NhaCungCap(models.Model):
    maNCC = models.CharField(max_length=50, primary_key=True)
    tenNCC = models.CharField(max_length=255)
    soDienThoai = models.CharField(max_length=15)
    email = models.EmailField()
    diaChi = models.TextField()

    class Meta:
        db_table = 'inventory_nhacungcap'
        constraints = [
            models.UniqueConstraint(fields=['soDienThoai'], name='ncc_unique_soDienThoai'),
            models.UniqueConstraint(fields=['email'], name='ncc_unique_email'),
        ]

    def __str__(self):
        return self.tenNCC
