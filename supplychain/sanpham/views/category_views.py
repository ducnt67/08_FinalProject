import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from sanpham.models import DanhMuc


def build_category_tree_list():
    """
    Tạo danh sách danh mục theo đúng thứ tự hiển thị:
    - Danh mục cha đứng trước
    - Danh mục con nằm ngay dưới danh mục cha
    - STT sẽ chạy tuần tự đúng theo danh sách này
    """

    parent_categories = DanhMuc.objects.filter(
        maDanhMucCha__isnull=True
    ).order_by('maDanhMuc')

    display_categories = []

    for parent in parent_categories:
        # Gắn thông tin phụ để template biết đây là danh mục cha
        parent.level = 0
        parent.display_order = len(display_categories) + 1
        display_categories.append(parent)

        child_categories = DanhMuc.objects.filter(
            maDanhMucCha=parent
        ).order_by('maDanhMuc')

        for child in child_categories:
            # Gắn thông tin phụ để template biết đây là danh mục con
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


def danhmuc(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            maDanhMuc = data.get('maDanhMuc')
            tenDanhMuc = data.get('tenDanhMuc')
            maDanhMucCha_id = data.get('maDanhMucCha')
            trangThai = data.get('trangThai', 1)

            if not tenDanhMuc:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tên danh mục không được để trống.'
                }, status=400)

            if not maDanhMuc:
                maDanhMuc = generate_category_code()

            parent_cat = None
            if maDanhMucCha_id:
                parent_cat = get_object_or_404(
                    DanhMuc,
                    maDanhMuc=maDanhMucCha_id
                )

                # Không cho danh mục tự chọn chính nó làm cha
                if maDanhMucCha_id == maDanhMuc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Danh mục không thể chọn chính nó làm danh mục cha.'
                    }, status=400)

            category, created = DanhMuc.objects.update_or_create(
                maDanhMuc=maDanhMuc,
                defaults={
                    'tenDanhMuc': tenDanhMuc,
                    'maDanhMucCha': parent_cat,
                    'trangThai': int(trangThai)
                }
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Lưu danh mục thành công!',
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

            category = get_object_or_404(DanhMuc, maDanhMuc=maDanhMuc)

            # Nếu danh mục có danh mục con thì không nên cho xóa trực tiếp
            if DanhMuc.objects.filter(maDanhMucCha=category).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Không thể xóa danh mục này vì vẫn còn danh mục con.'
                }, status=400)

            category.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Đã xóa danh mục!'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    # GET request
    categories = build_category_tree_list()

    # AJAX request: lấy dữ liệu để xem/sửa
    if (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        and 'maDanhMuc' in request.GET
    ):
        maDanhMuc = request.GET.get('maDanhMuc')
        category = get_object_or_404(DanhMuc, maDanhMuc=maDanhMuc)

        return JsonResponse({
            'maDanhMuc': category.maDanhMuc,
            'tenDanhMuc': category.tenDanhMuc,
            'maDanhMucCha': category.maDanhMucCha.maDanhMuc if category.maDanhMucCha else '',
            'trangThai': category.trangThai
        })

    return render(
        request,
        'sanpham/products/category_list.html',
        {
            'categories': categories
        }
    )