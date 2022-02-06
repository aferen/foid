from django.shortcuts import redirect
from django.contrib import messages, auth
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .forms import UserForm
from pages.decorators import is_admin
from django.contrib.auth.decorators import login_required

from users.models import User

def register(request):
  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      form.save()
      username = request.POST['username']
      user = get_object_or_404(User, username=username)
      user.set_password(user.password)
      user.save()
      messages.success(request, 'Kayıt işlemi tamamlandı.')
      return redirect('user_index')
    else:
      messages.error(request, 'Kayıt Olunamadı')

  form = UserForm()
  context = {'form': form}
  return render(request, 'users/register.html', context)

@is_admin
@login_required
def edituser(request, user_id):
  user = User.objects.get(pk=user_id)
  form = UserForm(instance=user)

  if request.method == 'POST':
    form = UserForm(request.POST, instance=user)
    if form.is_valid():
      form.save()
      user.set_password(user.password)
      user.save()
      messages.success(request, 'Kullanıcı kaydı güncellendi')
      return redirect('user_index')
    else:
      messages.error(request, 'Kullanıcı kaydı güncellenemedi')

  context = { 'form': form, 'item': user }
  return render(request, 'users/register.html', context)

@login_required
def profile(request):
  user_id = request.user.id
  print(user_id)
  user = User.objects.get(pk=user_id)
  form = UserForm(instance=user)

  if request.method == 'POST':
    form = UserForm(request.POST, instance=user)
    if form.is_valid():
      form.save()
      user.set_password(user.password)
      user.save()
      messages.success(request, 'Kullanıcı kaydı güncellendi')
      return redirect('/')
    else:
      messages.error(request, 'Kullanıcı kaydı güncellenemedi')

  context = { 'form': form, 'item': user }
  return render(request, 'users/profile.html', context)

@is_admin
@login_required
def deleteuser(request, user_id):
  user = User.objects.get(pk=user_id)
  if request.method == "POST":
      user.delete()
      return redirect('user_index')

  context = {'user': user}
  return render(request, 'users/delete.html', context)

def login(request):
  if request.method == 'POST':
    username = request.POST['username']
    password = request.POST['password']

    user = auth.authenticate(username=username, password=password)

    if user is not None:
      auth.login(request, user)
      messages.success(request, 'Giriş Başarılı')
      if user.is_admin:
        return redirect('user_index')
      else:
        return redirect('documents_index')
    else:
      messages.error(request, 'Kullanıcı adı veya şifre hatalı')
      return redirect('login')

  else:
    return render(request, 'users/login.html')

@login_required
def logout(request):
  if request.method == 'POST':
    auth.logout(request)
    messages.success(request, 'Çıkış başarılı')
    return redirect('/')

@is_admin
@login_required
def index(request):
  users = User.objects.order_by('username')

  paginator = Paginator(users, 20)
  page = request.GET.get('page')
  paged_users = paginator.get_page(page)

  context = {
    'users': paged_users
  }
  return render(request, 'users/index.html', context)


