from django.shortcuts import render
from django.http import HttpResponse
from objects.models import Objects

def index(request):
  return render(request, 'pages/index.html')

def about(request):
  objects = Objects.objects.all().order_by('objectID')
  context = {'objects': objects}
  return render(request, 'pages/about.html',context)

def error(request):
  return render(request, 'pages/error.html')

