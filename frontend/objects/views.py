from django.shortcuts import render
from django.contrib import messages, auth
from django.shortcuts import redirect
from objects.models import Objects
from objects.forms import ObjectsForm

from pages.decorators import is_admin
from django.contrib.auth.decorators import login_required
import random

@is_admin
@login_required
def index(request):
  objects = Objects.objects.all().order_by('objectID')
  context = {'objects': objects}
  return render(request, 'objects/index.html', context)


@is_admin
@login_required
def add(request):
  form = ObjectsForm()
  if request.method == 'POST':
    form = ObjectsForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Kayıt işlemi tamamlandı.')
    else:
      messages.error(request, 'Kayıt eklenemedi.')
    return redirect('object_index')
  context = {'form': form}
  return render(request, 'objects/add.html', context)

@is_admin
@login_required
def edit(request, object_id):
  object = Objects.objects.get(pk=object_id)
  form = ObjectsForm(instance=object)  
  form.id=object_id
  if request.method == 'POST':
    form = ObjectsForm(request.POST, instance=object)
    if form.is_valid():
      form.save()
      messages.success(request, 'Nesne kaydı güncellendi.')
    else:
      messages.error(request, 'Nesne kaydı güncellenemedi.')
    return redirect('object_index')

  context = { 'form': form, 'object': object }
  return render(request, 'objects/edit.html', context)

@is_admin
@login_required
def delete(request, object_id):
  object = Objects.objects.get(pk=object_id)
  if request.method == "POST":
    try:
      object.delete()
      messages.success(request, 'Nesne silindi.')
    except:
      messages.error(request, 'Nesne silinemedi.')
    return redirect('object_index')

  context = {'object': object}
  return render(request, 'objects/delete.html', context)

@is_admin
@login_required
def saveAllObject(request):
  cnt = 0
  Objects.objects.all().delete()
  objectsEN = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush', "bar chart", "line chart", "pie chart", ]
  objectsTR = ['insan', 'bisiklet', 'araba', 'motosiklet', 'uçak', 'otobüs', 'tren', 'kamyon', 'tekne', 'trafik lambası', 'yangın musluğu', 'dur işareti', 'parkmetre', 'bank', 'kuş', 'kedi', 'köpek', 'at', 'koyun', 'inek', 'fil', 'ayı', 'zebra', 'zürafa' , 'sırt çantası', 'şemsiye', 'el çantası', 'kravat', 'bavul', 'frizbi', 'kayak', 'snowboard', 'spor topu', 'uçurtma', 'beyzbol sopası', 'beyzbol eldiveni', 'kaykay', 'sörf tahtası', 'tenis raketi', 'şişe', 'şarap kadehi', 'bardak', 'çatal', 'bıçak', 'kaşık', 'kase', 'muz', 'elma', 'sandviç', 'portakal', 'brokoli', 'havuç', 'sosisli sandviç', 'pizza', 'çörek', 'kek', 'sandalye', 'kanepe', 'saksı bitkisi', 'yatak ', 'yemek masası', 'tuvalet', 'tv', 'dizüstü bilgisayar', 'fare', 'uzaktan kumanda', 'klavye', 'cep telefonu', 'mikrodalga', 'fırın', 'tost makinesi', 'lavabo', 'buzdolabı', 'kitap', 'saat', 'vazo', 'makas', 'oyuncak ayı', 'saç kurutma makinesi', 'diş fırçası', "bar grafik", "çizgi grafik", "pasta grafik"]
  for i in range(len(objectsEN)):
    if len(objectsEN) - i <= 3:
      id = 500 + cnt
      cnt = cnt +1
    else: 
      id = i
    color = "#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])
    object = Objects.objects.create(objectID=id,nameEN=objectsEN[i],nameTR=objectsTR[i],color=color)

  objects = Objects.objects.all().order_by('objectID')
  context = {'objects': objects}
  messages.success(request, 'Toplu nesne kaydı tamamlandı.')
  return render(request, 'objects/index.html', context)