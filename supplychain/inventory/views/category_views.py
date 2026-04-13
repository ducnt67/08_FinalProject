import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from inventory.models import DanhMuc

def danhmuc(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maDanhMuc = data.get('maDanhMuc')
            tenDanhMuc = data.get('tenDanhMuc')
            maDanhMucCha_id = data.get('maDanhMucCha')
            trangThai = data.get('trangThai', 1)
            
            if not maDanhMuc:
                # Generate new ID if not provided (create mode)
                last_cat = DanhMuc.objects.order_by('-maDanhMuc').first()
                if last_cat and last_cat.maDanhMuc.startswith('DM'):
                    last_num = int(last_cat.maDanhMuc.replace('DM', ''))
                    maDanhMuc = f"DM{str(last_num + 1).zfill(4)}"
                else:
                    maDanhMuc = "DM0001"
            
            parent_cat = None
            if maDanhMucCha_id:
                parent_cat = get_object_or_404(DanhMuc, maDanhMuc=maDanhMucCha_id)
                    
            category, created = DanhMuc.objects.update_or_create(
                maDanhMuc=maDanhMuc,
                defaults={
                    'tenDanhMuc': tenDanhMuc,
                    'maDanhMucCha': parent_cat,
                    'trangThai': int(trangThai)
                }
            )
            return JsonResponse({'status': 'success', 'message': 'Lưu danh mục thành công!', 'maDanhMuc': category.maDanhMuc})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maDanhMuc = data.get('maDanhMuc')
            category = get_object_or_404(DanhMuc, maDanhMuc=maDanhMuc)
            category.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa danh mục!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    categories = DanhMuc.objects.all().order_by('maDanhMuc')
    
    # Check if request is AJAX (for getting data for edit/view)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maDanhMuc' in request.GET:
        maDanhMuc = request.GET.get('maDanhMuc')
        category = get_object_or_404(DanhMuc, maDanhMuc=maDanhMuc)
        return JsonResponse({
            'maDanhMuc': category.maDanhMuc,
            'tenDanhMuc': category.tenDanhMuc,
            'maDanhMucCha': category.maDanhMucCha.maDanhMuc if category.maDanhMucCha else '',
            'trangThai': category.trangThai
        })

    return render(request, 'inventory/products/category_list.html', {'categories': categories})
