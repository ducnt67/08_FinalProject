import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from sanpham.models import ChiTiet_Sach, DanhMuc, SanPham
from nhacungcap.models import NhaCungCap


def _generate_product_code():
    last_sp = SanPham.objects.order_by('-maSP').first()

    if last_sp and last_sp.maSP.startswith('SP'):
        try:
            last_num = int(last_sp.maSP.replace('SP', ''))
            return f"SP{str(last_num + 1).zfill(3)}"
        except ValueError:
            return "SP001"

    return "SP001"


def _get_product_stock(product):
    """
    Lấy số lượng tồn từ bảng TonKho thông qua related_name='tonkho'.
    Nếu sản phẩm chưa có bản ghi tồn kho thì trả về 0.
    """
    try:
        return product.tonkho.soluongTon
    except Exception:
        return 0


def _get_book_detail(product):
    """
    Lấy thông tin chi tiết sách nếu sản phẩm có bản ghi ChiTiet_Sach.
    """
    try:
        chitiet = product.chitiet_sach
        return {
            'tacGia': chitiet.tacGia or '',
            'nhaXuatBan': chitiet.nhaXuatBan or '',
            'namXuatBan': chitiet.namXuatBan or ''
        }
    except Exception:
        return {
            'tacGia': '',
            'nhaXuatBan': '',
            'namXuatBan': ''
        }


def _get_inventory_positions(product):
    """
    Lấy chi tiết vị trí tồn kho nếu có TonKhoChiTiet.
    """
    chi_tiet_vi_tri = []

    try:
        for tkct in product.tonkhochitiet_set.select_related('viTri').filter(soluong__gt=0):
            chi_tiet_vi_tri.append({
                'maViTri': tkct.viTri.maViTri,
                'khuVuc': tkct.viTri.khuVuc,
                'keKho': tkct.viTri.keKho,
                'oChua': tkct.viTri.oChua,
                'soluong': tkct.soluong
            })
    except Exception:
        pass

    return chi_tiet_vi_tri


def _validate_product_category(danh_muc):
    """
    Rule nghiệp vụ:
    - Sản phẩm chỉ được gán vào danh mục con.
    - Danh mục con phải có trạng thái Đang hoạt động.
    """
    if danh_muc.maDanhMucCha is None:
        return False, 'Không thể gán sản phẩm vào danh mục cha. Vui lòng tạo hoặc chọn một danh mục con đang hoạt động để gán sản phẩm.'

    if danh_muc.trangThai != 1:
        return False, 'Sản phẩm chỉ được gán vào danh mục con đang hoạt động.'

    return True, ''


def sanpham(request):
    if request.method == 'POST':
        try:
            content_type = request.content_type or ''

            if 'application/json' in content_type:
                data = json.loads(request.body or '{}')
                uploaded_image = None
            else:
                data = request.POST
                uploaded_image = request.FILES.get('anhSP')

            maSP = (data.get('maSP') or '').strip()
            tenSP = (data.get('tenSP') or '').strip()
            danhMuc_id = (data.get('danhMuc') or '').strip()
            donViTinh = (data.get('donViTinh') or '').strip()
            giaBan = data.get('giaBan') or 0
            tonKhoToiThieu = data.get('tonKhoToiThieu') or 0
            nhaCungCap_id = (data.get('nhaCungCap') or '').strip()
            moTa = (data.get('moTa') or '').strip()
            trangThai = int(data.get('trangThai', 1))

            tacGia = (data.get('tacGia') or '').strip()
            nhaXuatBan = (data.get('nhaXuatBan') or '').strip()
            namXuatBan = int(data.get('namXuatBan') or 0)
            remove_image = str(data.get('removeImage', '0')) == '1'

            if not tenSP:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vui lòng nhập tên sản phẩm.'
                }, status=400)

            if not danhMuc_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vui lòng chọn danh mục con đang hoạt động.'
                }, status=400)

            if not donViTinh:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vui lòng chọn đơn vị tính.'
                }, status=400)

            if not nhaCungCap_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vui lòng chọn nhà cung cấp.'
                }, status=400)

            try:
                giaBan = float(giaBan)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Giá bán không hợp lệ.'
                }, status=400)

            if giaBan <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Giá bán phải lớn hơn 0.'
                }, status=400)

            try:
                tonKhoToiThieu = int(tonKhoToiThieu)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tồn kho tối thiểu không hợp lệ.'
                }, status=400)

            if tonKhoToiThieu < 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tồn kho tối thiểu không được nhỏ hơn 0.'
                }, status=400)

            if not maSP:
                maSP = _generate_product_code()

            danhMuc = get_object_or_404(
                DanhMuc,
                maDanhMuc=danhMuc_id
            )

            is_valid_category, category_message = _validate_product_category(danhMuc)
            if not is_valid_category:
                return JsonResponse({
                    'status': 'error',
                    'message': category_message
                }, status=400)

            nhaCungCap = get_object_or_404(
                NhaCungCap,
                maNCC=nhaCungCap_id
            )

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

            if tacGia or nhaXuatBan or namXuatBan:
                ChiTiet_Sach.objects.update_or_create(
                    sanPham=product,
                    defaults={
                        'tacGia': tacGia,
                        'nhaXuatBan': nhaXuatBan,
                        'namXuatBan': namXuatBan
                    }
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Lưu sản phẩm thành công!',
                'maSP': product.maSP
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maSP = data.get('maSP')

            product = get_object_or_404(
                SanPham,
                maSP=maSP
            )

            product.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Đã xóa sản phẩm!'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    # GET request
    products = SanPham.objects.select_related(
        'danhMuc',
        'danhMuc__maDanhMucCha',
        'nhaCungCap'
    ).order_by('maSP')

    for product in products:
        product.soluongTonValue = _get_product_stock(product)

    # Dùng cho bộ lọc ngoài bảng:
    # chỉ lấy danh mục con, không lấy danh mục cha.
    categories = DanhMuc.objects.filter(
        maDanhMucCha__isnull=False
    ).select_related(
        'maDanhMucCha'
    ).order_by(
        'maDanhMucCha__maDanhMuc',
        'maDanhMuc'
    )

    # Dùng cho form thêm/sửa sản phẩm:
    # chỉ cho chọn danh mục con đang hoạt động.
    active_child_categories = DanhMuc.objects.filter(
        maDanhMucCha__isnull=False,
        trangThai=1
    ).select_related(
        'maDanhMucCha'
    ).order_by(
        'maDanhMucCha__maDanhMuc',
        'maDanhMuc'
    )

    suppliers = NhaCungCap.objects.all().order_by('maNCC')

    # AJAX request: lấy dữ liệu để xem/sửa sản phẩm.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maSP' in request.GET:
        maSP = request.GET.get('maSP')
        product = get_object_or_404(
            SanPham.objects.select_related(
                'danhMuc',
                'danhMuc__maDanhMucCha',
                'nhaCungCap'
            ),
            maSP=maSP
        )

        book_detail = _get_book_detail(product)
        tonkho = _get_product_stock(product)
        chi_tiet_vi_tri = _get_inventory_positions(product)

        category_is_valid_for_edit = (
            product.danhMuc.maDanhMucCha is not None
            and product.danhMuc.trangThai == 1
        )

        return JsonResponse({
            'maSP': product.maSP,
            'tenSP': product.tenSP,
            'danhMuc': product.danhMuc.maDanhMuc,
            'tenDanhMuc': product.danhMuc.tenDanhMuc,
            'isDanhMucCon': product.danhMuc.maDanhMucCha is not None,
            'danhMucDangHoatDong': product.danhMuc.trangThai == 1,
            'categoryIsValidForEdit': category_is_valid_for_edit,
            'donViTinh': product.donViTinh,
            'giaBan': str(product.giaBan),
            'tonKhoToiThieu': product.tonKhoToiThieu,
            'nhaCungCap': product.nhaCungCap.maNCC,
            'tenNCC': product.nhaCungCap.tenNCC,
            'moTa': product.moTa or '',
            'trangThai': product.trangThai,
            'soluongTon': tonkho,
            'tacGia': book_detail['tacGia'],
            'nhaXuatBan': book_detail['nhaXuatBan'],
            'namXuatBan': book_detail['namXuatBan'],
            'anhSP': product.anhSP.url if product.anhSP else '',
            'chiTietViTri': chi_tiet_vi_tri
        })

    return render(
        request,
        'sanpham/products/san_pham.html',
        {
            'products': products,
            'categories': categories,
            'active_child_categories': active_child_categories,
            'suppliers': suppliers
        }
    )