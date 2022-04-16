from django.shortcuts import redirect
from django.contrib import messages, auth
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .forms import UserForm, UserEditForm
from pages.decorators import is_admin
from django.contrib.auth.decorators import login_required

from users.models import User

def register(request):
  form = UserForm()
  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      form.save()
      username = request.POST['username']
      user = get_object_or_404(User, username=username)
      user.set_password(user.password)
      user.save()
      messages.success(request, 'Kayıt işlemi tamamlandı. Giriş yapabilirsiniz.')
      return redirect('user_index')
    else:
      messages.error(request, 'Kayıt Olunamadı')

  context = {'form': form}
  return render(request, 'users/register.html', context)

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
def profile(request):
  user_id = request.user.id
  user = User.objects.get(pk=user_id)
  form = UserEditForm(instance=user)
  form.id=user_id
  if request.method == 'POST':
    form = UserEditForm(request.POST, instance=user)
    if form.is_valid():
      form.save()
      if form.cleaned_data['new_password']:
        user.set_password(form.cleaned_data['new_password'])
        user.save()
        messages.success(request, 'Profiliniz güncellendi. Şifrenizi de güncellendiğiniz için yeni şifreniz ile tekrar giriş yapınız.')
      else:
        messages.success(request, 'Kullanıcı kaydı güncellendi')
    else:
      messages.error(request, 'Kullanıcı kaydı güncellenemedi')
    return redirect('/')

  context = { 'form': form, 'item': user }
  return render(request, 'users/profile.html', context)

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

  context = {'users': users}
  return render(request, 'users/index.html', context)

@is_admin
@login_required
def add(request):
  form = UserForm()
  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      form.save()
      username = request.POST['username']
      user = get_object_or_404(User, username=username)
      user.set_password(user.password)
      user.save()
      messages.success(request, 'Kayıt işlemi tamamlandı.')
    else:
      messages.error(request, 'Kayıt eklenemedi.')
    return redirect('user_index')
  context = {'form': form}
  return render(request, 'users/add.html', context)

@is_admin
@login_required
def edit(request, user_id):
  user = User.objects.get(pk=user_id)
  form = UserEditForm(instance=user)  
  form.id=user_id
  if request.method == 'POST':
    form = UserEditForm(request.POST, instance=user)
    if form.is_valid():
      form.save()
      if form.cleaned_data['new_password']:
        user.set_password(form.cleaned_data['new_password'])
        user.save()
      messages.success(request, 'Kullanıcı kaydı güncellendi.')
    else:
      messages.error(request, 'Kullanıcı kaydı güncellenemedi.')
    return redirect('user_index')

  context = { 'form': form, 'item': user }
  return render(request, 'users/edit.html', context)

@is_admin
@login_required
def delete(request, user_id):
  user = User.objects.get(pk=user_id)
  if request.method == "POST":
    try:
      user.delete()
      messages.success(request, 'Kullanıcı silindi.')
    except:
      messages.error(request, 'Kullanıcı silinemedi.')
    return redirect('user_index')

  context = {'user': user}
  return render(request, 'users/delete.html', context)