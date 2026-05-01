from django.contrib import admin
from .models import DanhMuc, SanPham, ChiTiet_Sach

@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    list_display = ('maDanhMuc', 'tenDanhMuc', 'trangThai')
    search_fields = ('maDanhMuc', 'tenDanhMuc')

@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ('maSP', 'tenSP', 'danhMuc', 'nhaCungCap', 'giaBan', 'trangThai')
    search_fields = ('maSP', 'tenSP')
    list_filter = ('danhMuc', 'nhaCungCap', 'trangThai')

@admin.register(ChiTiet_Sach)
class ChiTietSachAdmin(admin.ModelAdmin):
    list_display = ('sanPham', 'tacGia', 'nhaXuatBan', 'namXuatBan')
    search_fields = ('sanPham__tenSP', 'tacGia')
