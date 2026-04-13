from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        username_req = request.POST.get('username')
        password_req = request.POST.get('password')

        user = authenticate(request, username=username_req, password=password_req)

        if user is not None:
            login(request, user)
            return redirect('inventory:tongquan')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không chính xác.')
            return render(request, 'inventory/auth/login.html')

    return render(request, 'inventory/auth/login.html')