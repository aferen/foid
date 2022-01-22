from django.shortcuts import render
from django.contrib import messages


def is_admin(func):

    def is_admin_user(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not user.is_admin:
            messages.error(request, 'Sayfaya Erişim Yetkiniz Yok!')
            return render(
                request, 'pages/error.html'
            )
        return func(request, *args, **kwargs)
    return is_admin_user
