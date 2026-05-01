import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from nhacungcap.models import NhaCungCap
from django.core.exceptions import ValidationError

def ncc(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maNCC = data.get('maNCC')
            tenNCC = data.get('tenNCC')
            soDienThoai = data.get('soDienThoai')
            email = data.get('email')
            diaChi = data.get('diaChi')
            
            if not maNCC:
                # Generate new ID if not provided (create mode)
                last_ncc = NhaCungCap.objects.order_by('-maNCC').first()
                if last_ncc:
                    last_num = int(last_ncc.maNCC.replace('NCC', ''))
                    maNCC = f"NCC{str(last_num + 1).zfill(3)}"
                else:
                    maNCC = "NCC001"
                    
            supplier, created = NhaCungCap.objects.update_or_create(
                maNCC=maNCC,
                defaults={
                    'tenNCC': tenNCC,
                    'soDienThoai': soDienThoai,
                    'email': email,
                    'diaChi': diaChi
                }
            )
            return JsonResponse({'status': 'success', 'message': 'Lưu nhà cung cấp thành công!', 'maNCC': supplier.maNCC})
        except Exception as e:
            # Trích xuất thông báo lỗi thân thiện
            if hasattr(e, 'message_dict'):
                messages = [str(m[0] if isinstance(m, list) else m) for m in e.message_dict.values()]
                error_msg = ". ".join(messages)
            elif hasattr(e, 'messages'):
                error_msg = ". ".join([str(m) for m in e.messages])
            else:
                error_msg = str(e)
                
            # Loại bỏ các ký tự thừa nếu str(e) vẫn còn dạng dict/list
            error_msg = error_msg.replace("{", "").replace("}", "").replace("[", "").replace("]", "").replace("'", "")
            
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maNCC = data.get('maNCC')
            supplier = get_object_or_404(NhaCungCap, maNCC=maNCC)
            
            from inventory.models import DonDatHang
            if DonDatHang.objects.filter(nhaCungCap=supplier).exists():
                return JsonResponse({'status': 'error', 'message': 'Không thể xóa nhà cung cấp này vì đã có dữ liệu giao dịch (đơn đặt hàng).'}, status=400)
                
            supplier.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa nhà cung cấp!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    suppliers = NhaCungCap.objects.all().order_by('maNCC')
    
    # Check if request is AJAX (for getting data for edit/view)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maNCC' in request.GET:
        maNCC = request.GET.get('maNCC')
        supplier = get_object_or_404(NhaCungCap, maNCC=maNCC)
        return JsonResponse({
            'maNCC': supplier.maNCC,
            'tenNCC': supplier.tenNCC,
            'soDienThoai': supplier.soDienThoai,
            'email': supplier.email,
            'diaChi': supplier.diaChi
        })

    return render(request, 'inventory/suppliers/supplier_list.html', {'suppliers': suppliers})
