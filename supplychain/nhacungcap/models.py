from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# 2. Nhà cung cấp
class NhaCungCap(models.Model):
    maNCC = models.CharField(max_length=50, primary_key=True)
    tenNCC = models.CharField(max_length=255)
    soDienThoai = models.CharField(
        max_length=20, 
        unique=True,
        error_messages={
            'unique': 'Số điện thoại này đã tồn tại trong hệ thống.'
        },
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s.-]{9,20}$',
                message="Số điện thoại không hợp lệ."
            )
        ]
    )
    email = models.EmailField(
        unique=True,
        error_messages={
            'invalid': 'Địa chỉ email không hợp lệ.',
            'unique': 'Email này đã tồn tại trong hệ thống.'
        }
    )
    diaChi = models.TextField()

    class Meta:
        db_table = 'inventory_nhacungcap'
        constraints = [
            models.UniqueConstraint(fields=['soDienThoai'], name='ncc_unique_soDienThoai_v2'),
            models.UniqueConstraint(fields=['email'], name='ncc_unique_email_v2'),
        ]

    def clean(self):
        if self.tenNCC: self.tenNCC = self.tenNCC.strip()
        if self.soDienThoai: self.soDienThoai = self.soDienThoai.strip()
        if self.email: self.email = self.email.strip()
        if self.diaChi: self.diaChi = self.diaChi.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tenNCC
