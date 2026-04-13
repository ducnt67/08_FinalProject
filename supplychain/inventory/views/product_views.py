import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from inventory.models import ChiTiet_Sach, DanhMuc, NhaCungCap, SanPham

def sanpham(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maSP = data.get('maSP')
            tenSP = data.get('tenSP')
            danhMuc_id = data.get('danhMuc')
            donViTinh = data.get('donViTinh')
            giaBan = data.get('giaBan')
            tonKhoToiThieu = data.get('tonKhoToiThieu', 0)
            nhaCungCap_id = data.get('nhaCungCap')
            moTa = data.get('moTa', '')
            trangThai = data.get('trangThai', 1)
            
            # Additional fields for Book details
            tacGia = data.get('tacGia', '')
            nhaXuatBan = data.get('nhaXuatBan', '')
            namXuatBan = data.get('namXuatBan', 0)
            
            if not maSP:
                # Generate new ID if not provided (create mode)
                last_sp = SanPham.objects.order_by('-maSP').first()
                if last_sp and last_sp.maSP.startswith('SP'):
                    last_num = int(last_sp.maSP.replace('SP', ''))
                    maSP = f"SP{str(last_num + 1).zfill(3)}"
                else:
                    maSP = "SP001"
            
            danhMuc = get_object_or_404(DanhMuc, maDanhMuc=danhMuc_id)
            nhaCungCap = get_object_or_404(NhaCungCap, maNCC=nhaCungCap_id)
                    
            product, created = SanPham.objects.update_or_create(
                maSP=maSP,
                defaults={
                    'tenSP': tenSP,
                    'danhMuc': danhMuc,
                    'donViTinh': donViTinh,
                    'giaBan': giaBan,
                    'tonKhoToiThieu': tonKhoToiThieu,
                    'nhaCungCap': nhaCungCap,
                    'moTa': moTa,
                    'trangThai': int(trangThai)
                }
            )
            
            # Update or create book details if any
            if tacGia or nhaXuatBan or namXuatBan:
                ChiTiet_Sach.objects.update_or_create(
                    sanPham=product,
                    defaults={
                        'tacGia': tacGia,
                        'nhaXuatBan': nhaXuatBan,
                        'namXuatBan': namXuatBan
                    }
                )
                
            return JsonResponse({'status': 'success', 'message': 'Lưu sản phẩm thành công!', 'maSP': product.maSP})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maSP = data.get('maSP')
            product = get_object_or_404(SanPham, maSP=maSP)
            product.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa sản phẩm!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    products = SanPham.objects.select_related('danhMuc', 'nhaCungCap').prefetch_related('tonkho', 'chitiet_sach').order_by('maSP')
    categories = DanhMuc.objects.all()
    suppliers = NhaCungCap.objects.all()
    
    # Check if request is AJAX (for getting data for edit/view)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maSP' in request.GET:
        maSP = request.GET.get('maSP')
        product = get_object_or_404(SanPham, maSP=maSP)
        
        # Lấy số lượng tồn từ model TonKho nếu có
        try:
            tonkho = product.tonkho.soluongTon
        except:
            tonkho = 0
            
        # Lấy thông tin sách nếu có
        try:
            chitiet = product.chitiet_sach
            tacGia = chitiet.tacGia
            nhaXuatBan = chitiet.nhaXuatBan
            namXuatBan = chitiet.namXuatBan
        except:
            tacGia = ''
            nhaXuatBan = ''
            namXuatBan = ''
            
        return JsonResponse({
            'maSP': product.maSP,
            'tenSP': product.tenSP,
            'danhMuc': product.danhMuc.maDanhMuc,
            'donViTinh': product.donViTinh,
            'giaBan': str(product.giaBan),
            'tonKhoToiThieu': product.tonKhoToiThieu,
            'nhaCungCap': product.nhaCungCap.maNCC,
            'moTa': product.moTa,
            'trangThai': product.trangThai,
            'soluongTon': tonkho,
            'tacGia': tacGia,
            'nhaXuatBan': nhaXuatBan,
            'namXuatBan': namXuatBan
        })

    return render(request, 'inventory/products/product_list.html', {
        'products': products,
        'categories': categories,
        'suppliers': suppliers
    })
