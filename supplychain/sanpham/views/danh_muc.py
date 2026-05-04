import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from khohang.models import TonKho
from sanpham.models import DanhMuc, SanPham


# Hàm xử lý danh sách
def build_category_tree_list():
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
    last_cat = DanhMuc.objects.order_by('-maDanhMuc').first()

    if last_cat and last_cat.maDanhMuc.startswith('DM'):
        try:
            last_num = int(last_cat.maDanhMuc.replace('DM', ''))
            return f"DM{str(last_num + 1).zfill(4)}"
        except ValueError:
            return "DM0001"

    return "DM0001"


def is_duplicate_category_name(ten_danh_muc, parent_cat, current_ma_danh_muc=None):
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

            if category.trangThai != 1:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ được chỉnh sửa danh mục đang hoạt động.'
                }, status=400)

            if category.maDanhMucCha is None and parent_cat is not None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Danh mục cha không được thay đổi danh mục cha.'
                }, status=400)

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

                active_child_exists = child_categories.filter(

                    trangThai=1

                ).exists()

                if active_child_exists:
                    return JsonResponse({

                        'status': 'error',

                        'message': 'Không thể xóa hoặc chuyển danh mục cha sang Ngừng hoạt động vì vẫn còn danh mục con đang hoạt động.'

                    }, status=400)

                has_child_categories = child_categories.exists()

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

                if not has_child_categories and not parent_has_any_products:
                    category.delete()

                    return JsonResponse({

                        'status': 'success',

                        'message': 'Xóa danh mục cha thành công!'

                    })

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

            if not has_any_products:
                category.delete()

                return JsonResponse({

                    'status': 'success',

                    'message': 'Xóa danh mục con thành công!'

                })

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

        # Danh sách sản phẩm.
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
