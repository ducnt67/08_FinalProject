from django.contrib import admin
from .models import (
    ViTriKho, LoHang, TonKho, NhapKho, PhieuNhap_CT, 
    XuatKho, PhieuXuat_CT, KiemKe, KiemKe_CT, 
    TraHangNCC, TraHangNCC_CT, TonKhoChiTiet
)

@admin.register(ViTriKho)
class ViTriKhoAdmin(admin.ModelAdmin):
    list_display = ('maViTri', 'khuVuc', 'keKho', 'oChua')
    search_fields = ('maViTri', 'khuVuc')

@admin.register(LoHang)
class LoHangAdmin(admin.ModelAdmin):
    list_display = ('maLo', 'sanPham', 'ngaySanXuat', 'hanSuDung', 'ngayNhapVao')
    search_fields = ('maLo', 'sanPham__tenSP')

@admin.register(TonKho)
class TonKhoAdmin(admin.ModelAdmin):
    list_display = ('sanPham', 'soluongTon', 'trangthaiCanhBao')
    list_filter = ('trangthaiCanhBao',)

class PhieuNhap_CTInline(admin.TabularInline):
    model = PhieuNhap_CT
    extra = 1

@admin.register(NhapKho)
class NhapKhoAdmin(admin.ModelAdmin):
    list_display = ('maPhieuNhap', 'nhaCungCap', 'ngayNhap', 'trangthaiNhap', 'tongtienNhap')
    list_filter = ('trangthaiNhap', 'nhaCungCap')
    search_fields = ('maPhieuNhap',)
    inlines = [PhieuNhap_CTInline]

class PhieuXuat_CTInline(admin.TabularInline):
    model = PhieuXuat_CT
    extra = 1

@admin.register(XuatKho)
class XuatKhoAdmin(admin.ModelAdmin):
    list_display = ('maPhieuXuat', 'ngayXuat', 'noiXuat', 'trangThai')
    list_filter = ('trangThai',)
    search_fields = ('maPhieuXuat',)
    inlines = [PhieuXuat_CTInline]

@admin.register(TonKhoChiTiet)
class TonKhoChiTietAdmin(admin.ModelAdmin):
    list_display = ('sanPham', 'viTri', 'soluong')
    list_filter = ('viTri',)
