from django.contrib import admin
from .models import DonDatHang, DonDatHang_CT

class DonDatHang_CTInline(admin.TabularInline):
    model = DonDatHang_CT
    extra = 1

@admin.register(DonDatHang)
class DonDatHangAdmin(admin.ModelAdmin):
    list_display = ('maDatHang', 'nhaCungCap', 'ngayDatHang', 'trangThai', 'nguoiLap')
    list_filter = ('trangThai', 'nhaCungCap')
    search_fields = ('maDatHang', 'nhaCungCap__tenNCC')
    inlines = [DonDatHang_CTInline]
