import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from inventory.models import ChiTiet_Sach, DanhMuc, NhaCungCap, SanPham


def _generate_product_code():
    last_sp = SanPham.objects.order_by('-maSP').first()
    if last_sp and last_sp.maSP.startswith('SP'):
        try:
            last_num = int(last_sp.maSP.replace('SP', ''))
            return f"SP{str(last_num + 1).zfill(3)}"
        except ValueError:
            return "SP001"
    return "SP001"

def sanpham(request):
    if request.method == 'POST':
        try:
            # Support both legacy JSON payload and multipart/form-data (image upload).
            content_type = request.content_type or ''
            if 'application/json' in content_type:
                data = json.loads(request.body or '{}')
                uploaded_image = None
            else:
                data = request.POST
                uploaded_image = request.FILES.get('anhSP')

            maSP = (data.get('maSP') or '').strip()
            tenSP = (data.get('tenSP') or '').strip()
            danhMuc_id = data.get('danhMuc')
            donViTinh = (data.get('donViTinh') or '').strip()
            giaBan = data.get('giaBan') or 0
            tonKhoToiThieu = data.get('tonKhoToiThieu') or 0
            nhaCungCap_id = data.get('nhaCungCap')
            moTa = (data.get('moTa') or '').strip()
            trangThai = int(data.get('trangThai', 1))

            # Additional fields for book details.
            tacGia = (data.get('tacGia') or '').strip()
            nhaXuatBan = (data.get('nhaXuatBan') or '').strip()
            namXuatBan = int(data.get('namXuatBan') or 0)
            remove_image = str(data.get('removeImage', '0')) == '1'

            if not maSP:
                maSP = _generate_product_code()

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
                    'trangThai': trangThai
                }
            )

            if remove_image and product.anhSP:
                product.anhSP.delete(save=False)
                product.anhSP = None

            if uploaded_image:
                product.anhSP = uploaded_image

            if remove_image or uploaded_image:
                product.save()

            # Update or create book details if any.
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
            'namXuatBan': namXuatBan,
            'anhSP': product.anhSP.url if product.anhSP else ''
        })

    return render(request, 'inventory/products/product_list.html', {
        'products': products,
        'categories': categories,
        'suppliers': suppliers
    })
