import itertools
from functools import reduce
import operator
from pydoc import doc

from tika import parser
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .forms import DocumentsForm
from frontend.settings import MEDIA_ROOT
import os

from documents.models import *
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
  user = request.user
  if not user.is_admin:
    documents = Documents.objects.all().filter(Q(user=user)).order_by('-id')    
  else:
    documents = Documents.objects.all().order_by('-id')

  for doc in documents:
    searchHistory = SearchHistory.objects.filter(Q(document=doc)).order_by('pk').last()
    doc.query = searchHistory.query
    doc.modified_date = searchHistory.modified_date
    
  paginator = Paginator(documents, 20)
  page = request.GET.get('page')
  paged_documents = paginator.get_page(page)

  context = {'documents': paged_documents}
  return render(request, 'documents/index.html', context)

@login_required
def search(request):
  user = request.user
  form = DocumentsForm(user=user)
  if request.method == 'POST':
    form = DocumentsForm(request.POST, request.FILES, user=user)
    if form.is_valid():
      document = form.save(commit=False)
      document.name = document.path.file.name
      document.save()
      query = form.data.get('query')
      SearchHistory.objects.create(document=document, query=query)

      # file_path = t_obj.thesis_doc.field.storage.base_location
      #file_path = t_obj.documents_doc.file.name
      #path, file_name = os.path.split(file_path)
      #Documents.objects.create()

      return redirect('documents_index')

  context = {'document': form}
  return render(request, 'documents/search.html', context)

@login_required
def searchById(request, document_id):
  user = request.user
  form = DocumentsForm(user=user)
  if not user.is_admin:
    document = Documents.objects.get(Q(id=document_id), Q(user=user))
  else:
    document = Documents.objects.get(Q(id=document_id))
  form.id = document.id
  form.path = document.id
  form.docID = document.docID
  if request.method == 'POST':
    form = DocumentsForm(request.POST, request.FILES, user=user)
    if form.is_valid():
      query = form.data.get('query')
      SearchHistory.objects.create(document=document, query=query)

      # file_path = t_obj.thesis_doc.field.storage.base_location
      #file_path = t_obj.documents_doc.file.name
      #path, file_name = os.path.split(file_path)
      #Documents.objects.create()

      return redirect('documents_detail', document_id)

  context = {'document': form, 'document_id': form.id}
  return render(request, 'documents/searchById.html', context)

@login_required
def detail(request, document_id):
  user = request.user
  if not user.is_admin:
    document = Documents.objects.get(Q(id=document_id), Q(user=user))
  else:
    document = Documents.objects.get(Q(id=document_id))
  searchHistory = SearchHistory.objects.filter(Q(document=document)).order_by('-id') 
  context = {'document':document, 'searchHistory': searchHistory}
  return render(request, 'documents/details.html', context)

@login_required
def delete(request, document_id):
  user = request.user
  if not user.is_admin:
    document = Documents.objects.get(Q(id=document_id), Q(user=user))
  else:
    document = Documents.objects.get(Q(id=document_id))
  if request.method == "POST":
    try:
      document.delete()
      messages.success(request, 'Doküman silindi.')
    except:
      messages.error(request, 'Doküman silinemedi.')
    return redirect('documents_index')

  context = {'document':document}
  return render(request, 'documents/delete.html', context)

@login_required
def deleteSearchHistory(request, history_id):
  user = request.user
  if not user.is_admin:
    history = SearchHistory.objects.get(Q(id=history_id), Q(user=user))
  else:
    history = SearchHistory.objects.get(Q(id=history_id))
  if request.method == "POST":
    try:
      history.delete()
      messages.success(request, 'Arama kaydı silindi.')
    except:
      messages.error(request, 'Arama kaydı silinemedi.')
    return redirect('documents_detail', history.document.id)

  context = {'history':history}
  return render(request, 'documents/deleteSearchHistory.html', context)