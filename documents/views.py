import itertools
from functools import reduce
import operator

from tika import parser
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .forms import DocumentsForm
from foid.settings import MEDIA_ROOT
import os

from documents.models import *
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
  user = request.user
  if not user.is_admin:
    documents = Documents.objects.all().filter(Q(userID=user)).order_by('-id')
  else:
    documents = Documents.objects.all().order_by('-id')

  paginator = Paginator(documents, 20)
  page = request.GET.get('page')
  paged_documents = paginator.get_page(page)

  if user.is_admin:
    usernames = User.objects.order_by().values('id', 'username')
  else:
    usernames = User.objects.order_by().filter(pk=user.id).values('id', 'username')
  context = {
    'documents': paged_documents,
    'uname': usernames,
  }
  return render(request, 'documents/index.html', context)

@login_required
def search(request):
  user = request.user
  form = DocumentsForm(user=user)
  if request.method == 'POST':
    form = DocumentsForm(request.POST, request.FILES, user=user)
    if form.is_valid():
      obj = form.save(commit=False)
      obj.name = obj.path.file.name
      obj.save()

      # file_path = t_obj.thesis_doc.field.storage.base_location
      #file_path = t_obj.documents_doc.file.name
      #path, file_name = os.path.split(file_path)
      #Documents.objects.create()

      return redirect('documents_index')

  context = {'form': form}
  return render(request, 'documents/search.html', context)