import json
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from inventory.models import (
    DanhMuc,
    DonDatHang,
    KiemKe,
    KiemKe_CT,
    NhaCungCap,
    NhapKho,
    PhieuNhap_CT,
    PhieuXuat_CT,
    SanPham,
    TonKho,
    TraHangNCC,
    TraHangNCC_CT,
    XuatKho,
)

def tonkho(request):
    inventory_items = TonKho.objects.select_related('sanPham').all()
    return render(request, 'inventory/inventory/stock_overview.html', {'inventory_items': inventory_items})

def nhapkho(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maPhieuNhap = data.get('maPhieuNhap')
            nhaCungCap_name = data.get('nhaCungCap')
            ngayNhap = data.get('ngayNhap')
            ghichu = data.get('ghichu', '')
            items = data.get('items', [])
            donDatHang_id = data.get('donDatHang')
            trangthaiNhap = int(data.get('trangThai', 0)) 
            
            # Lay ban ghi cu neu co de kiem tra trang thai
            old_record = NhapKho.objects.filter(maPhieuNhap=maPhieuNhap).first()
            old_trangthai = old_record.trangthaiNhap if old_record else None
            
            if not items:
                return JsonResponse({'status': 'error', 'message': 'Phiếu nhập phải có ít nhất 1 sản phẩm.'}, status=400)

            # --- TU DONG SINH MA PHIEU NHAP NEU TRONG ---
            if not maPhieuNhap:
                today_str = timezone.now().strftime('%Y%m%d')
                prefix = f"PNK-{today_str}-"
                last_record = NhapKho.objects.filter(maPhieuNhap__startswith=prefix).order_by('-maPhieuNhap').first()
                if last_record:
                    try:
                        last_num = int(last_record.maPhieuNhap.split('-')[-1])
                        maPhieuNhap = f"{prefix}{str(last_num + 1).zfill(3)}"
                    except:
                        maPhieuNhap = f"{prefix}001"
                else:
                    maPhieuNhap = f"{prefix}001"
            
            # Lay nha cung cap
            try:
                nhaCungCap = NhaCungCap.objects.get(tenNCC=nhaCungCap_name)
            except NhaCungCap.DoesNotExist:
                nhaCungCap = get_object_or_404(NhaCungCap, maNCC=nhaCungCap_name)
            
            donDatHang = None
            if donDatHang_id:
                donDatHang = get_object_or_404(DonDatHang, maDatHang=donDatHang_id)

            # Tinh tong tien
            tongtienNhap = sum(Decimal(str(item['price'])) * int(item['qty']) for item in items)
            
            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(ngayNhap) if ngayNhap else timezone.now()
            
            import_record, created = NhapKho.objects.update_or_create(
                maPhieuNhap=maPhieuNhap,
                defaults={
                    'nhaCungCap': nhaCungCap,
                    'ngayNhap': parsed_date,
                    'trangthaiNhap': trangthaiNhap,
                    'ghichu': ghichu,
                    'donDatHang': donDatHang,
                    'tongtienNhap': tongtienNhap
                }
            )
            
            if not created:
                # Neu sửa phiếu đã Hoàn thành, phải hoàn tác tồn kho cũ trước
                if old_trangthai == 1:
                    for old_ct in import_record.phieunhap_ct_set.all():
                        tk, _ = TonKho.objects.get_or_create(sanPham=old_ct.sanPham)
                        tk.soluongTon -= old_ct.soluongThucNhan
                        tk.save()
                import_record.phieunhap_ct_set.all().delete()
                
            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                qty = int(item['qty'])
                price = Decimal(str(item['price']))
                ordered_qty = int(item.get('orderedQty', qty))
                
                PhieuNhap_CT.objects.create(
                    phieuNhap=import_record,
                    sanPham=sanPham,
                    soluongDat=ordered_qty,
                    dongiaNhap=price,
                    thanhTien=qty * price,
                    soluongThucNhan=qty
                )
                
                
                # Cập nhật tồn kho nếu là trạng thái Hoàn thành (1)
                if trangthaiNhap == 1:
                    tonkho_obj, _ = TonKho.objects.get_or_create(sanPham=sanPham)
                    tonkho_obj.soluongTon += qty
                    tonkho_obj.save()
            
            # Neu nhap theo PO và là Hoàn thành, cap nhat trang thai PO thanh "Hoan thanh" (1)
            if donDatHang and trangthaiNhap == 1:
                donDatHang.trangThai = 1
                donDatHang.save()
                
            msg = "Đã hoàn thành phiếu nhập!" if trangthaiNhap == 1 else "Đã lưu phiếu tạm!"
                
            return JsonResponse({'status': 'success', 'message': msg, 'maPhieuNhap': import_record.maPhieuNhap})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maPhieuNhap = data.get('maPhieuNhap')
            import_record = get_object_or_404(NhapKho, maPhieuNhap=maPhieuNhap)
            
            if import_record.trangthaiNhap == 1:
                return JsonResponse({'status': 'error', 'message': 'Không thể xóa/hủy phiếu đã hoàn thành.'}, status=400)
            
            if import_record.trangthaiNhap == -1:
                return JsonResponse({'status': 'error', 'message': 'Phiếu đã được hủy trước đó.'}, status=400)
                        
            # Chuyển trạng thái thành Đã hủy (-1) thay vì xóa thật
            import_record.trangthaiNhap = -1
            import_record.save()
            return JsonResponse({'status': 'success', 'message': 'Đã hủy phiếu nhập thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    # GET request
    inbound_records = NhapKho.objects.select_related('nhaCungCap').prefetch_related('phieunhap_ct_set__sanPham').order_by('-ngayNhap')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maPhieuNhap' in request.GET:
        maPhieuNhap = request.GET.get('maPhieuNhap')
        record = get_object_or_404(NhapKho, maPhieuNhap=maPhieuNhap)
        
        items = []
        for ct in record.phieunhap_ct_set.all():
            items.append({
                'maSP': ct.sanPham.maSP,
                'tenSP': ct.sanPham.tenSP,
                'danhMuc': ct.sanPham.danhMuc.tenDanhMuc if ct.sanPham.danhMuc else '',
                'donViTinh': ct.sanPham.donViTinh,
                'orderedQty': ct.soluongDat,
                'qty': ct.soluongThucNhan,
                'price': str(ct.dongiaNhap),
                'amount': str(ct.thanhTien)
            })
            
        status_map = {0: 'Phiếu tạm', 1: 'Hoàn thành', -1: 'Đã hủy'}
        status_class_map = { 0: 'bg-yellow-100 text-yellow-700', 1: 'bg-green-100 text-green-700', -1: 'bg-red-100 text-red-700' }
            
        return JsonResponse({
            'maPhieuNhap': record.maPhieuNhap,
            'ngayNhap': record.ngayNhap.strftime('%Y-%m-%dT%H:%M') if record.ngayNhap else '',
            'ngayNhapDisplay': record.ngayNhap.strftime('%d/%m/%Y %H:%M') if record.ngayNhap else '',
            'nhaCungCap': record.nhaCungCap.tenNCC,
            'nhaCungCapCode': record.nhaCungCap.maNCC,
            'ghichu': record.ghichu,
            'donDatHang': record.donDatHang.maDatHang if record.donDatHang else '',
            'trangThai': status_map.get(record.trangthaiNhap, 'Unknown'),
            'trangThaiClass': status_class_map.get(record.trangthaiNhap, ''),
            'user': 'Admin',
            'items': items
        })

    suppliers = NhaCungCap.objects.all()
    products = SanPham.objects.select_related('danhMuc').all()
    
    # Lay danh sach PO trang thai "Dang giao" (2)
    pos = DonDatHang.objects.filter(trangThai=2).select_related('nhaCungCap').prefetch_related('dondathang_ct_set__sanPham')
    po_list = []
    for po in pos:
        po_list.append({
            'code': po.maDatHang,
            'supplier': po.nhaCungCap.tenNCC,
            'items': [
                {
                    'code': ct.sanPham.maSP,
                    'name': ct.sanPham.tenSP,
                    'price': float(ct.giaNhap),
                    'orderedQty': ct.soluongDat
                } for ct in po.dondathang_ct_set.all()
            ]
        })

    # Lay danh sach phieu tra hang
    return_records = TraHangNCC.objects.select_related('nhaCungCap', 'phieuNhap').all().order_by('-ngayTra')
    
    return render(request, 'inventory/inventory/stock_in_list.html', {
        'inbound_records': inbound_records,
        'return_records': return_records,
        'suppliers': suppliers,
        'products': products,
        'purchase_orders_json': json.dumps(po_list)
    })

def trahang(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maPhieuNhap = data.get('maPhieuNhap')
            items = data.get('items', [])
            
            import_record = get_object_or_404(NhapKho, maPhieuNhap=maPhieuNhap)
            
            if import_record.trangthaiNhap != 1:
                return JsonResponse({'status': 'error', 'message': 'Chỉ có thể tạo phiếu trả hàng cho phiếu nhập đã hoàn thành.'}, status=400)
            
            # Generate TraHangNCC
            today_str = timezone.now().strftime('%Y%m%d')
            prefix = f"PTH-{today_str}-"
            last_record = TraHangNCC.objects.filter(maPhieuTra__startswith=prefix).order_by('-maPhieuTra').first()
            if last_record:
                try:
                    last_num = int(last_record.maPhieuTra.split('-')[-1])
                    maPhieuTra = f"{prefix}{str(last_num + 1).zfill(3)}"
                except:
                    maPhieuTra = f"{prefix}001"
            else:
                maPhieuTra = f"{prefix}001"
                
            trangThai = int(data.get('trangThai', 0))
            
            tongtienTra = sum(Decimal(str(item['price'])) * int(item['qty']) for item in items)
            
            tra_hang = TraHangNCC.objects.create(
                maPhieuTra=maPhieuTra,
                nhaCungCap=import_record.nhaCungCap,
                ngayTra=timezone.now(),
                phieuNhap=import_record,
                trangThai=trangThai,
                tongtienTra=tongtienTra
            )
            
            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                qty = int(item['qty'])
                price = Decimal(str(item['price']))
                
                TraHangNCC_CT.objects.create(
                    phieuTra=tra_hang,
                    sanPham=sanPham,
                    soluongTra=qty,
                    dongiaTra=price,
                    thanhTien=qty * price,
                    lydoTra=item.get('reason', 'Hang loi')
                )
                
                # Chỉ trừ tồn kho nếu là Đã trả hàng (1)
                if trangThai == 1:
                    tonkho_obj, _ = TonKho.objects.get_or_create(sanPham=sanPham)
                    tonkho_obj.soluongTon -= qty
                    if tonkho_obj.soluongTon < 0: tonkho_obj.soluongTon = 0
                    tonkho_obj.save()
                
            msg = f'Xác nhận trả hàng {maPhieuTra} thành công!' if trangThai == 1 else f'Đã lưu phiếu tạm {maPhieuTra}!'
            return JsonResponse({'status': 'success', 'message': msg})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    elif request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            maPhieuTra = data.get('maPhieuTra')
            items = data.get('items', [])
            
            tra_hang = get_object_or_404(TraHangNCC, maPhieuTra=maPhieuTra)
            
            if tra_hang.trangThai == 1:
                return JsonResponse({'status': 'error', 'message': 'Không thể sửa phiếu đã hoàn thành.'}, status=400)
            
            trangThai = int(data.get('trangThai', 0))
            
            # Xoa chi tiet cu (Vì là phiếu tạm nên chưa trừ kho, không cần hoàn tồn)
            tra_hang.trahangncc_ct_set.all().delete()
            
            # Cập nhật tổng tiền và trạng thái
            tongtienTra = sum(Decimal(str(item['price'])) * int(item['qty']) for item in items)
            tra_hang.tongtienTra = tongtienTra
            tra_hang.trangThai = trangThai
            tra_hang.save()
            
            # Tạo chi tiết mới
            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                qty = int(item['qty'])
                price = Decimal(str(item['price']))
                
                TraHangNCC_CT.objects.create(
                    phieuTra=tra_hang,
                    sanPham=sanPham,
                    soluongTra=qty,
                    dongiaTra=price,
                    thanhTien=qty * price,
                    lydoTra=item.get('reason', 'Hàng lỗi')
                )
                
                # Chỉ trừ tồn kho nếu chuyển sang Đã trả hàng (1)
                if trangThai == 1:
                    tonkho_obj, _ = TonKho.objects.get_or_create(sanPham=sanPham)
                    tonkho_obj.soluongTon -= qty
                    if tonkho_obj.soluongTon < 0: tonkho_obj.soluongTon = 0
                    tonkho_obj.save()
            
            msg = f'Xác nhận trả hàng {maPhieuTra} thành công!' if trangThai == 1 else f'Đã cập nhật phiếu tạm {maPhieuTra}!'
            return JsonResponse({'status': 'success', 'message': msg})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            tra_hang = get_object_or_404(TraHangNCC, maPhieuTra=maPhieuTra)
            
            if tra_hang.trangThai == 1:
                return JsonResponse({'status': 'error', 'message': 'Không thể hủy phiếu đã hoàn thành.'}, status=400)
            
            if tra_hang.trangThai == -1:
                return JsonResponse({'status': 'error', 'message': 'Phiếu đã được hủy trước đó.'}, status=400)
            
            # Chuyển trạng thái sang Đã hủy (-1) thay vì xóa thật
            tra_hang.trangThai = -1
            tra_hang.save()
            return JsonResponse({'status': 'success', 'message': 'Đã hủy phiếu trả hàng thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # Xu ly lay chi tiet phieu tra qua AJAX
    elif request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maPhieuTra' in request.GET:
        maPhieuTra = request.GET.get('maPhieuTra')
        record = get_object_or_404(TraHangNCC, maPhieuTra=maPhieuTra)
        
        items = []
        for ct in record.trahangncc_ct_set.all():
            # Lấy số lượng thực nhận từ phiếu nhập gốc
            original_qty = 0
            if record.phieuNhap:
                try:
                    original_ct = record.phieuNhap.phieunhap_ct_set.get(sanPham=ct.sanPham)
                    original_qty = original_ct.soluongThucNhan
                except:
                    original_qty = 0
            
            items.append({
                'maSP': ct.sanPham.maSP,
                'tenSP': ct.sanPham.tenSP,
                'donViTinh': ct.sanPham.donViTinh,
                'qty': ct.soluongTra,
                'originalQty': original_qty,
                'price': str(ct.dongiaTra),
                'amount': str(ct.thanhTien),
                'reason': ct.lydoTra
            })
            
        status_map = {0: 'Phiếu tạm', 1: 'Đã trả hàng', -1: 'Đã hủy'}
        status_class_map = { 0: 'bg-yellow-100 text-yellow-700', 1: 'bg-green-100 text-green-700', -1: 'bg-red-100 text-red-700' }

        return JsonResponse({
            'maPhieuTra': record.maPhieuTra,
            'ngayTraDisplay': record.ngayTra.strftime('%d/%m/%Y %H:%M') if record.ngayTra else '',
            'nhaCungCap': record.nhaCungCap.tenNCC,
            'phieuNhapGoc': record.phieuNhap.maPhieuNhap if record.phieuNhap else 'N/A',
            'tongTien': str(record.tongtienTra),
            'trangThai': record.trangThai,
            'trangThaiDisplay': status_map.get(record.trangThai, 'Không xác định'),
            'trangThaiClass': status_class_map.get(record.trangThai, ''),
            'items': items
        })

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def xuatkho(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maPhieuXuat = data.get('maPhieuXuat')
            ngayXuat = data.get('ngayXuat')
            noiXuat = data.get('noiXuat')
            trangThai = int(data.get('trangThai', 0)) # Mac dinh la Nhap (0)
            items = data.get('items', [])

            if not items and trangThai != -1:
                return JsonResponse({'status': 'error', 'message': 'Phiếu xuất phải có ít nhất 1 sản phẩm.'}, status=400)

            if not maPhieuXuat:
                today_str = timezone.now().strftime('%Y%m%d')
                prefix = f"PXK-{today_str}-"
                last_record = XuatKho.objects.filter(maPhieuXuat__startswith=prefix).order_by('-maPhieuXuat').first()
                if last_record:
                    try:
                        last_num = int(last_record.maPhieuXuat.split('-')[-1])
                        maPhieuXuat = f"{prefix}{str(last_num + 1).zfill(3)}"
                    except:
                        maPhieuXuat = f"{prefix}001"
                else:
                    maPhieuXuat = f"{prefix}001"

            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(ngayXuat) if ngayXuat else timezone.now()

            # Lay ban ghi cu neu co de so sanh trang thai
            old_record = XuatKho.objects.filter(maPhieuXuat=maPhieuXuat).first()
            old_trang_thai = old_record.trangThai if old_record else None

            export_record, created = XuatKho.objects.update_or_create(
                maPhieuXuat=maPhieuXuat,
                defaults={
                    'ngayXuat': parsed_date,
                    'noiXuat': noiXuat,
                    'trangThai': trangThai
                }
            )

            # Neu chuyen tu trang thai khac sang Hoan thanh (1), hoac cap nhat khi dang Hoan thanh
            if not created:
                # Neu cu la Hoan thanh, hoan lai kho de tinh toan moi
                if old_trang_thai == 1:
                    for old_ct in export_record.phieuxuat_ct_set.all():
                        tk, _ = TonKho.objects.get_or_create(sanPham=old_ct.sanPham)
                        tk.soluongTon += old_ct.soluongXuat
                        tk.save()
                export_record.phieuxuat_ct_set.all().delete()

            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                qty = int(item['qty'])

                PhieuXuat_CT.objects.create(
                    phieuXuat=export_record,
                    sanPham=sanPham,
                    soluongXuat=qty
                )

                # Tru ton kho neu trang thai la Hoan thanh (1)
                if trangThai == 1:
                    tonkho_obj, _ = TonKho.objects.get_or_create(sanPham=sanPham)
                    tonkho_obj.soluongTon -= qty
                    if tonkho_obj.soluongTon < 0: tonkho_obj.soluongTon = 0
                    tonkho_obj.save()

            if trangThai == 1:
                msg = "Đã xuất kho thành công!"
            elif trangThai == -1:
                msg = "Đã hủy phiếu xuất!"
            else:
                msg = "Đã lưu nháp phiếu xuất!"

            return JsonResponse({'status': 'success', 'message': msg, 'maPhieuXuat': export_record.maPhieuXuat})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maPhieuXuat = data.get('maPhieuXuat')
            export_record = get_object_or_404(XuatKho, maPhieuXuat=maPhieuXuat)

            if export_record.trangThai == 1:
                for ct in export_record.phieuxuat_ct_set.all():
                    try:
                        tonkho_obj = TonKho.objects.get(sanPham=ct.sanPham)
                        tonkho_obj.soluongTon += ct.soluongXuat
                        tonkho_obj.save()
                    except TonKho.DoesNotExist:
                        pass

            export_record.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa phiếu xuất!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    outbound_records = XuatKho.objects.prefetch_related('phieuxuat_ct_set__sanPham').order_by('-ngayXuat')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maPhieuXuat' in request.GET:
        maPhieuXuat = request.GET.get('maPhieuXuat')
        record = get_object_or_404(XuatKho, maPhieuXuat=maPhieuXuat)

        items = []
        for ct in record.phieuxuat_ct_set.all():
            items.append({
                'maSP': ct.sanPham.maSP,
                'tenSP': ct.sanPham.tenSP,
                'donViTinh': ct.sanPham.donViTinh,
                'qty': ct.soluongXuat
            })

        status_map = {0: 'Nháp', 1: 'Hoàn thành', -1: 'Hủy'}
        status_class_map = { 0: 'bg-gray-100 text-gray-700', 1: 'bg-green-100 text-green-700', -1: 'bg-red-100 text-red-700' }

        return JsonResponse({
            'maPhieuXuat': record.maPhieuXuat,
            'ngayXuat': record.ngayXuat.strftime('%Y-%m-%dT%H:%M') if record.ngayXuat else '',
            'ngayXuatDisplay': record.ngayXuat.strftime('%d/%m/%Y %H:%M') if record.ngayXuat else '',
            'noiXuat': record.noiXuat,
            'trangThai': record.trangThai,
            'trangThaiDisplay': status_map.get(record.trangThai, 'Không xác định'),
            'trangThaiClass': status_class_map.get(record.trangThai, ''),
            'items': items
        })

    products = SanPham.objects.all()
    return render(request, 'inventory/inventory/stock_out_list.html', {
        'outbound_records': outbound_records,
        'products': products
    })

def kiemke(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            maKiemKe = data.get('maKiemKe')
            nguoiKiem = data.get('nguoiKiem', 'Admin')
            ngayKiem = data.get('ngayKiem')
            trangThai = int(data.get('trangThai', 0))
            items = data.get('items', [])

            if not items:
                return JsonResponse({'status': 'error', 'message': 'Phiếu kiểm kê phải có ít nhất 1 sản phẩm.'}, status=400)

            if not maKiemKe:
                today_str = timezone.now().strftime('%Y%m%d')
                prefix = f"PKK-{today_str}-"
                last_record = KiemKe.objects.filter(maKiemKe__startswith=prefix).order_by('-maKiemKe').first()
                if last_record:
                    try:
                        last_num = int(last_record.maKiemKe.split('-')[-1])
                        maKiemKe = f"{prefix}{str(last_num + 1).zfill(3)}"
                    except:
                        maKiemKe = f"{prefix}001"
                else:
                    maKiemKe = f"{prefix}001"

            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(ngayKiem) if ngayKiem else timezone.now()

            check_record, created = KiemKe.objects.update_or_create(
                maKiemKe=maKiemKe,
                defaults={
                    'ngayKiem': parsed_date,
                    'nguoiKiem': nguoiKiem,
                    'trangThai': trangThai
                }
            )

            if not created:
                check_record.kiemke_ct_set.all().delete()

            for item in items:
                sanPham = get_object_or_404(SanPham, maSP=item['maSP'])
                slTonKho = int(item['slTonKho'])
                slThucTe = int(item['slThucTe'])

                KiemKe_CT.objects.create(
                    kiemKe=check_record,
                    sanPham=sanPham,
                    slTonKho=slTonKho,
                    slThucTe=slThucTe
                )

                # Cap nhat ton kho neu trang thai la Da can bang (1)
                if trangThai == 1:
                    tonkho_obj, _ = TonKho.objects.get_or_create(sanPham=sanPham)
                    tonkho_obj.soluongTon = slThucTe
                    tonkho_obj.save()

            msg = "Đã lưu phiếu kiểm kê!" if trangThai == 0 else "Đã cân bằng kho thành công!"
            return JsonResponse({'status': 'success', 'message': msg, 'maKiemKe': check_record.maKiemKe})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            maKiemKe = data.get('maKiemKe')
            check_record = get_object_or_404(KiemKe, maKiemKe=maKiemKe)
            check_record.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa phiếu kiểm kê!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'maKiemKe' in request.GET:
        maKiemKe = request.GET.get('maKiemKe')
        record = get_object_or_404(KiemKe, maKiemKe=maKiemKe)
        
        items = []
        for ct in record.kiemke_ct_set.all():
            items.append({
                'maSP': ct.sanPham.maSP,
                'tenSP': ct.sanPham.tenSP,
                'donViTinh': ct.sanPham.donViTinh,
                'slTonKho': ct.slTonKho,
                'slThucTe': ct.slThucTe,
                'chenhLech': ct.slThucTe - ct.slTonKho
            })
            
        status_map = {0: 'Đang kiểm', 1: 'Đã cân bằng', -1: 'Đã hủy'}
        status_class_map = { 0: 'bg-yellow-100 text-yellow-700', 1: 'bg-green-100 text-green-700', -1: 'bg-red-100 text-red-700' }
            
        return JsonResponse({
            'maKiemKe': record.maKiemKe,
            'ngayKiem': record.ngayKiem.strftime('%Y-%m-%dT%H:%M') if record.ngayKiem else '',
            'ngayKiemDisplay': record.ngayKiem.strftime('%d/%m/%Y %H:%M') if record.ngayKiem else '',
            'nguoiKiem': record.nguoiKiem,
            'trangThai': record.trangThai,
            'trangThaiDisplay': status_map.get(record.trangThai, 'Không xác định'),
            'trangThaiClass': status_class_map.get(record.trangThai, ''),
            'items': items
        })

    inventory_checks = KiemKe.objects.prefetch_related('kiemke_ct_set__sanPham').order_by('-ngayKiem')
    products = SanPham.objects.all()
    categories = DanhMuc.objects.all()
    
    # Lay thong tin ton kho hien tai cho tung san pham
    stock_data = {}
    for tk in TonKho.objects.all():
        stock_data[tk.sanPham_id] = tk.soluongTon
        
    return render(request, 'inventory/inventory/stock_check_list.html', {
        'inventory_checks': inventory_checks,
        'products': products,
        'categories': categories,
        'stock_data_json': json.dumps(stock_data)
    })

