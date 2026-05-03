import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from sanpham.models import DanhMuc, SanPham
from khohang.models import TonKho


def build_category_tree_list():
    """
    Tạo danh sách danh mục theo đúng thứ tự hiển thị:
    - Danh mục cha đứng trước
    - Danh mục con nằm ngay dưới danh mục cha
    - STT sẽ được xử lý lại ở frontend khi lọc
    """

    parent_categories = DanhMuc.objects.filter(
        maDanhMucCha__isnull=True
    ).order_by('maDanhMuc')

    display_categories = []

    for parent in parent_categories:
        parent.level = 0
        parent.display_order = len(display_categories) + 1
        display_categories.append(parent)

        child_categories = DanhMuc.objects.filter(
            maDanhMucCha=parent
        ).order_by('maDanhMuc')

        for child in child_categories:
            child.level = 1
            child.display_order = len(display_categories) + 1
            display_categories.append(child)

    return display_categories


def generate_category_code():
    """
    Sinh mã danh mục tự động dạng DM0001, DM0002,...
    """

    last_cat = DanhMuc.objects.order_by('-maDanhMuc').first()

    if last_cat and last_cat.maDanhMuc.startswith('DM'):
        try:
            last_num = int(last_cat.maDanhMuc.replace('DM', ''))
            return f"DM{str(last_num + 1).zfill(4)}"
        except ValueError:
            return "DM0001"

    return "DM0001"


def is_duplicate_category_name(ten_danh_muc, parent_cat, current_ma_danh_muc=None):
    """
    Kiểm tra trùng tên danh mục trong cùng một danh mục cha.

    Quy tắc:
    - Không cho phép trùng tên trong cùng cấp cha.
    - Khi chỉnh sửa thì loại trừ chính danh mục hiện tại.
    """

    query = DanhMuc.objects.filter(
        tenDanhMuc__iexact=ten_danh_muc,
        maDanhMucCha=parent_cat
    )

    if current_ma_danh_muc:
        query = query.exclude(maDanhMuc=current_ma_danh_muc)

    return query.exists()


def danhmuc(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            maDanhMuc = data.get('maDanhMuc')
            tenDanhMuc = data.get('tenDanhMuc')
            maDanhMucCha_id = data.get('maDanhMucCha')

            if not tenDanhMuc or not str(tenDanhMuc).strip():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tên danh mục không được để trống.'
                }, status=400)

            tenDanhMuc = str(tenDanhMuc).strip()

            parent_cat = None

            if maDanhMucCha_id:
                parent_cat = get_object_or_404(
                    DanhMuc,
                    maDanhMuc=maDanhMucCha_id
                )

                # Hệ thống chỉ hỗ trợ 2 cấp:
                # Danh mục cha và danh mục con.
                # Vì vậy danh mục cha được chọn không được là danh mục con.
                if parent_cat.maDanhMucCha is not None:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Chỉ được chọn danh mục cha cấp gốc.'
                    }, status=400)

                # Không cho danh mục tự chọn chính nó làm cha.
                if maDanhMuc and maDanhMucCha_id == maDanhMuc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Danh mục không thể chọn chính nó làm danh mục cha.'
                    }, status=400)

            # =====================================================
            # TRƯỜNG HỢP 1: THÊM MỚI DANH MỤC
            # =====================================================
            if not maDanhMuc:
                if is_duplicate_category_name(tenDanhMuc, parent_cat):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Đã tồn tại tên danh mục này, nhập tên khác để tiếp tục.'
                    }, status=400)

                maDanhMuc = generate_category_code()

                category = DanhMuc.objects.create(
                    maDanhMuc=maDanhMuc,
                    tenDanhMuc=tenDanhMuc,
                    maDanhMucCha=parent_cat,
                    trangThai=1
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Tạo danh mục thành công!',
                    'maDanhMuc': category.maDanhMuc
                })

            # =====================================================
            # TRƯỜNG HỢP 2: CHỈNH SỬA DANH MỤC
            # =====================================================
            category = get_object_or_404(
                DanhMuc,
                maDanhMuc=maDanhMuc
            )

            # Theo đặc tả: chỉ chỉnh sửa danh mục có trạng thái Đang hoạt động.
            if category.trangThai != 1:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ được chỉnh sửa danh mục đang hoạt động.'
                }, status=400)

            # Theo đặc tả: danh mục cha không cho phép thay đổi danh mục cha.
            if category.maDanhMucCha is None and parent_cat is not None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Danh mục cha không được thay đổi danh mục cha.'
                }, status=400)

            # Theo đặc tả: danh mục con không được chuyển thành danh mục cha.
            if category.maDanhMucCha is not None and parent_cat is None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Danh mục con không được chuyển thành danh mục cha.'
                }, status=400)

            if is_duplicate_category_name(tenDanhMuc, parent_cat, current_ma_danh_muc=maDanhMuc):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Đã tồn tại tên danh mục này, nhập tên khác để tiếp tục.'
                }, status=400)

            category.tenDanhMuc = tenDanhMuc
            category.maDanhMucCha = parent_cat

            # KHÔNG cập nhật category.trangThai tại chức năng chỉnh sửa.
            # Trạng thái chỉ được thay đổi thông qua luồng xóa/ngừng hoạt động.
            category.save(update_fields=['tenDanhMuc', 'maDanhMucCha'])

            return JsonResponse({
                'status': 'success',
                'message': 'Cập nhật danh mục thành công!',
                'maDanhMuc': category.maDanhMuc
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


    elif request.method == 'DELETE':

        try:

            data = json.loads(request.body)

            maDanhMuc = data.get('maDanhMuc')

            category = get_object_or_404(

                DanhMuc,

                maDanhMuc=maDanhMuc

            )

            is_parent_category = category.maDanhMucCha is None

            # =====================================================

            # TRƯỜNG HỢP 1: XỬ LÝ DANH MỤC CHA

            # =====================================================

            if is_parent_category:

                child_categories = DanhMuc.objects.filter(

                    maDanhMucCha=category

                )

                # Ràng buộc mới:

                # Danh mục cha không thể xóa hoặc chuyển sang Ngừng hoạt động

                # nếu vẫn còn danh mục con có trạng thái Đang hoạt động.

                active_child_exists = child_categories.filter(

                    trangThai=1

                ).exists()

                if active_child_exists:
                    return JsonResponse({

                        'status': 'error',

                        'message': 'Không thể xóa hoặc chuyển danh mục cha sang Ngừng hoạt động vì vẫn còn danh mục con đang hoạt động.'

                    }, status=400)

                has_child_categories = child_categories.exists()

                # Phòng trường hợp dữ liệu bị gán trực tiếp sản phẩm vào danh mục cha.

                # Theo đặc tả, sản phẩm chỉ nên được gán vào danh mục con,

                # nhưng check thêm để tránh lỗi dữ liệu.

                parent_has_active_products = SanPham.objects.filter(

                    danhMuc=category,

                    trangThai=1

                ).exists()

                if parent_has_active_products:
                    return JsonResponse({

                        'status': 'error',

                        'message': 'Không thể xóa hoặc chuyển danh mục cha sang Ngừng hoạt động vì vẫn còn sản phẩm đang bán.'

                    }, status=400)

                parent_has_any_products = SanPham.objects.filter(

                    danhMuc=category

                ).exists()

                child_has_any_products = SanPham.objects.filter(

                    danhMuc__in=child_categories

                ).exists()

                # Nếu không còn danh mục con và không còn sản phẩm nào liên quan

                # => cho phép xóa cứng danh mục cha.

                if not has_child_categories and not parent_has_any_products:
                    category.delete()

                    return JsonResponse({

                        'status': 'success',

                        'message': 'Xóa danh mục cha thành công!'

                    })

                # Đến đây nghĩa là:

                # - Không còn danh mục con đang hoạt động

                # - Nhưng vẫn còn danh mục con ngừng hoạt động hoặc dữ liệu liên quan

                # => không xóa cứng, chuyển chính danh mục cha sang Ngừng hoạt động.

                if category.trangThai == 0:
                    return JsonResponse({

                        'status': 'success',

                        'message': 'Danh mục cha hiện đã ở trạng thái Ngừng hoạt động.'

                    })

                category.trangThai = 0

                category.save(update_fields=['trangThai'])

                return JsonResponse({

                    'status': 'success',

                    'message': 'Danh mục cha còn ràng buộc dữ liệu nên đã được chuyển sang trạng thái Ngừng hoạt động.'

                })

            # =====================================================

            # TRƯỜNG HỢP 2: XỬ LÝ DANH MỤC CON

            # =====================================================

            # Ràng buộc mới:

            # Danh mục con không thể xóa hoặc chuyển sang Ngừng hoạt động

            # nếu vẫn còn sản phẩm có trạng thái Đang bán.

            active_product_exists = SanPham.objects.filter(

                danhMuc=category,

                trangThai=1

            ).exists()

            if active_product_exists:
                return JsonResponse({

                    'status': 'error',

                    'message': 'Không thể xóa hoặc chuyển danh mục con sang Ngừng hoạt động vì vẫn còn sản phẩm đang bán.'

                }, status=400)

            has_any_products = SanPham.objects.filter(

                danhMuc=category

            ).exists()

            # Nếu danh mục con không còn sản phẩm nào

            # => cho phép xóa cứng.

            if not has_any_products:
                category.delete()

                return JsonResponse({

                    'status': 'success',

                    'message': 'Xóa danh mục con thành công!'

                })

            # Nếu danh mục con không còn sản phẩm Đang bán,

            # nhưng vẫn còn sản phẩm khác, ví dụ Ngừng bán

            # => không xóa cứng, chuyển danh mục con sang Ngừng hoạt động.

            if category.trangThai == 0:
                return JsonResponse({

                    'status': 'success',

                    'message': 'Danh mục con hiện đã ở trạng thái Ngừng hoạt động.'

                })

            category.trangThai = 0

            category.save(update_fields=['trangThai'])

            return JsonResponse({

                'status': 'success',

                'message': 'Danh mục con không còn sản phẩm đang bán nên đã được chuyển sang trạng thái Ngừng hoạt động.'

            })


        except Exception as e:

            return JsonResponse({

                'status': 'error',

                'message': str(e)

            }, status=400)

    # =====================================================
    # GET REQUEST
    # =====================================================
    categories = build_category_tree_list()

    # AJAX request: lấy dữ liệu để xem/sửa.
    if (
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
            and 'maDanhMuc' in request.GET
    ):
        maDanhMuc = request.GET.get('maDanhMuc')

        category = get_object_or_404(
            DanhMuc,
            maDanhMuc=maDanhMuc
        )

        products = []

        # Chỉ danh mục con mới có danh sách sản phẩm.
        if category.maDanhMucCha is not None:
            product_queryset = SanPham.objects.filter(
                danhMuc=category
            ).order_by('maSP')

            product_ids = [product.maSP for product in product_queryset]

            tonkho_map = {
                tonkho.sanPham_id: tonkho.soluongTon
                for tonkho in TonKho.objects.filter(
                    sanPham_id__in=product_ids
                )
            }

            for product in product_queryset:
                products.append({
                    'maSP': product.maSP,
                    'tenSP': product.tenSP,
                    'soLuongTon': tonkho_map.get(product.maSP, 0)
                })

        return JsonResponse({
            'maDanhMuc': category.maDanhMuc,
            'tenDanhMuc': category.tenDanhMuc,
            'maDanhMucCha': category.maDanhMucCha.maDanhMuc if category.maDanhMucCha else '',
            'tenDanhMucCha': category.maDanhMucCha.tenDanhMuc if category.maDanhMucCha else '',
            'trangThai': category.trangThai,
            'isChild': category.maDanhMucCha is not None,
            'products': products
        })

    return render(
        request,
        'sanpham/products/danh_muc.html',
        {
            'categories': categories
        }
    )
