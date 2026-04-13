import json
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from inventory.models import DonDatHang, DonDatHang_CT, NhaCungCap, SanPham

def dathang(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maDatHang = data.get('maDatHang')
            nhaCungCap_id = data.get('nhaCungCap')
            ghiChu = data.get('ghiChu', '')
            items = data.get('items', [])
            trangThai_text = data.get('trangThai', 'Chờ xác nhận')
            
            # Map status text to integer
            status_map = {
                'Chờ xác nhận': 0,
                'Hoàn thành': 1,
                'Đang giao': 2,
                'Đã hủy': 3
            }
            trangThai = status_map.get(trangThai_text, 0)
            
            if not items:
                return JsonResponse({'status': 'error', 'message': 'Đơn hàng phải có ít nhất 1 sản phẩm.'}, status=400)
            
            if not maDatHang:
                # Generate new ID if not provided (create mode)
                last_order = DonDatHang.objects.order_by('-maDatHang').first()
                if last_order and last_order.maDatHang.startswith('PO'):
                    last_num = int(last_order.maDatHang.split('-')[-1])
                    maDatHang = f"PO-{timezone.now().year}-{str(last_num + 1).zfill(3)}"
                else:
                    maDatHang = f"PO-{timezone.now().year}-001"
            
            nhaCungCap = get_object_or_404(NhaCungCap, maNCC=nhaCungCap_id)
            
            # Update or create Order
            order, created = DonDatHang.objects.update_or_create(
                maDatHang=maDatHang,
                defaults={
                    'nhaCungCap': nhaCungCap,
                    'trangThai': trangThai,
                    'ghiChu': ghiChu
                }
            )
            
            # Delete existing items if updating
            if not created:
                order.dondathang_ct_set.all().delete()
                
            # Create new items
            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                qty = int(item['qty'])
                price = Decimal(item['price'])
                DonDatHang_CT.objects.create(
                    donDatHang=order,
                    sanPham=sanPham,
                    soluongDat=qty,
                    giaNhap=price,
                    thanhTien=qty * price
                )
                
            return JsonResponse({'status': 'success', 'message': 'Lưu đơn đặt hàng thành công!', 'maDatHang': order.maDatHang})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maDatHang = data.get('maDatHang')
            order = get_object_or_404(DonDatHang, maDatHang=maDatHang)
            order.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa đơn đặt hàng!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            maDatHang = data.get('maDatHang')
            trangThai_text = data.get('trangThai')
            order = get_object_or_404(DonDatHang, maDatHang=maDatHang)
            
            status_map = {
                'Chờ xác nhận': 0,
                'Hoàn thành': 1,
                'Đang giao': 2,
                'Đã hủy': 3
            }
            if trangThai_text in status_map:
                order.trangThai = status_map[trangThai_text]
                order.save()
                return JsonResponse({'status': 'success', 'message': 'Đã cập nhật trạng thái!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Trạng thái không hợp lệ'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    purchase_orders = DonDatHang.objects.select_related('nhaCungCap').prefetch_related('dondathang_ct_set__sanPham__danhMuc').order_by('-ngayDatHang')
    
    # Compute totals for each order
    for order in purchase_orders:
        order.total_amount = sum(ct.thanhTien for ct in order.dondathang_ct_set.all())
        
    suppliers = NhaCungCap.objects.all()
    products = SanPham.objects.select_related('danhMuc', 'nhaCungCap').all()
    
    # Check if request is AJAX (for getting data for edit/view)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maDatHang' in request.GET:
        maDatHang = request.GET.get('maDatHang')
        order = get_object_or_404(DonDatHang, maDatHang=maDatHang)
        items = []
        for ct in order.dondathang_ct_set.all():
            items.append({
                'maSP': ct.sanPham.maSP,
                'tenSP': ct.sanPham.tenSP,
                'danhMuc': ct.sanPham.danhMuc.tenDanhMuc,
                'qty': ct.soluongDat,
                'price': str(ct.giaNhap),
                'amount': str(ct.thanhTien)
            })
            
        status_reverse_map = {
            0: 'Chờ xác nhận',
            1: 'Hoàn thành',
            2: 'Đang giao',
            3: 'Đã hủy'
        }
        status_class_map = {
            0: 'status-warning',
            1: 'status-success',
            2: 'status-info',
            3: 'status-danger'
        }
            
        return JsonResponse({
            'maDatHang': order.maDatHang,
            'ngayDatHang': order.ngayDatHang.strftime('%Y-%m-%d'),
            'nhaCungCap': order.nhaCungCap.maNCC,
            'ghiChu': order.ghiChu,
            'trangThai': status_reverse_map.get(order.trangThai, 'Chờ xác nhận'),
            'trangThaiClass': status_class_map.get(order.trangThai, 'status-warning'),
            'items': items
        })

    return render(request, 'inventory/orders/order_list.html', {
        'purchase_orders': purchase_orders,
        'suppliers': suppliers,
        'products': products,
    })
