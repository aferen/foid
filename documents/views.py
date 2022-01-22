import itertools
from functools import reduce
import operator

from tika import parser
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .forms import documentsForm
from .lecturer import Lecturer
from yazilimlab.settings import MEDIA_ROOT
import os

from document.models import *
from django.contrib.auth.decorators import login_required

import ocrmypdf

@login_required
def adddocuments(request):
  user = request.user
  form = documentsForm(user=user)
  if request.method == 'POST':
    print(request.POST)
    form = documentsForm(request.POST, request.FILES, user=user)
    if form.is_valid():
      t_obj = form.save(commit=False)
      #file_name = t_obj.documents_doc.file.name
      
      # file_path = t_obj.documents_doc.field.storage.base_location

      t_obj.save()
      file_path = t_obj.documents_doc.file.name
      path, file_name = os.path.split(file_path)
      created = readPDF(request, t_obj.id, file_name)
      if created:
        messages.success(request, 'Tez dokumanı eklendi!')
      else:
        messages.error(request, 'Tez dokumanı eklenemedi. Daha önce eklenmiş!')

      return redirect('documents_index')

  context = {'form': form}
  return render(request, 'documents/fileupload.html', context)

@login_required
def index(request):
  user = request.user
  if not user.is_admin:
    theses = documents.objects.all().filter(Q(admin_user=user)).order_by('-id')
  else:
    theses = documents.objects.all().order_by('-id')

  paginator = Paginator(theses, 20)
  page = request.GET.get('page')
  paged_documents = paginator.get_page(page)

  projectterms = documents.objects.values('documents_term').annotate(dcount=Count('documents_term')).order_by()
  projectnames = documents.objects.values('class_name').annotate(dcount=Count('class_name')).order_by()
  if user.is_admin:
    usernames = User.objects.order_by().values('id', 'username')
  else:
    usernames = User.objects.order_by().filter(pk=user.id).values('id', 'username')
  context = {
    'theses': paged_documents,
    'pterm': projectterms,
    'cname': projectnames,
    'uname': usernames,
  }
  return render(request, 'documents/index.html', context)

@login_required
def documents(request, documents_id):
  documents = get_object_or_404(documents, pk=documents_id)

  context = {
    'theses': documents
  }
  return render(request, 'documents/documents.html', context)

@login_required
def deletedocuments(request, documents_id):
  documents = documents.objects.get(id=documents_id)
  if request.method == "POST":
      documents.delete()
      return redirect('documents_index')

  context = {'documents':documents}
  return render(request, 'documents/delete.html', context)

@login_required
def documentsDetails(request, documents_id):
  user = request.user
  documents = documents.objects.get(Q(id=documents_id), Q(admin_user=user))
  jury = Jury.objects.filter(jury_documents=documents)
  student = Student.objects.filter(student_documents=documents)
  keyword = Keyword.objects.filter(keyword_documents=documents)

  context = {'documents':documents, 'juries': jury, 'students': student, 'keywords': keyword}
  return render(request, 'documents/details.html', context)

@login_required
def firstsearch(request):
  if request.method == 'POST':
    student_name = request.POST['studentname']
    key_words = request.POST['kwords']
    class_name = request.POST['clsname']
    project_name = request.POST['projectname']
    project_term = request.POST['projectterm']

    queryset_documents = documents.objects.order_by('-id')
    queryset_student = Student.objects.order_by('-id')
    queryset_keyword = Keyword.objects.order_by('-id')
    array_list = []
    if class_name:
      queryset_list1 = queryset_documents.filter(class_name__icontains=class_name).values_list('pk', flat=True)
      array_list = list(itertools.chain(array_list, queryset_list1))

    if project_name:
      queryset_list2 = queryset_documents.filter(documents_title__icontains=project_name).values_list('pk', flat=True)
      array_list = list(itertools.chain(array_list, queryset_list2))
    if project_term:
      queryset_list3 = queryset_documents.filter(documents_term__icontains=project_term).values_list('pk', flat=True)
      array_list = list(itertools.chain(array_list, queryset_list3))

    if student_name:
      queryset_list4 = queryset_student.filter(Q(student_name__icontains=student_name)).values_list('student_documents', flat=True)
      array_list = list(itertools.chain(array_list, queryset_list4))

    key_array = []
    if key_words:
      key_arr = key_words.split(',')
      for key in key_arr:
        if len(key) > 0:
          key_array.append(key.strip())

    if len(key_array) > 0:
      queryset_list5 = queryset_keyword.filter(reduce(operator.or_, (Q(keyword__icontains=x) for x in key_array))).values_list('keyword_documents', flat=True)
      array_list = list(itertools.chain(array_list, queryset_list5))

    last_list = [i for n, i in enumerate(array_list) if i not in array_list[:n]]

    user = request.user
    if not user.is_admin:
      theses = documents.objects.filter(Q(pk__in=last_list), Q(admin_user=user)).order_by('-id')
    else:
      theses = documents.objects.filter(Q(pk__in=last_list)).order_by('-id')

    # theses = documents.objects.filter(Q(pk__in=last_list), Q(admin_user=user)).order_by('-id')
    paginator = Paginator(theses, 20)
    page = request.GET.get('page')
    paged_documents = paginator.get_page(page)

    projectterms = documents.objects.values('documents_term').annotate(dcount=Count('documents_term')).order_by()
    projectnames = documents.objects.values('class_name').annotate(dcount=Count('class_name')).order_by()
    if user.is_admin:
      usernames = User.objects.order_by().values('id', 'username')
    else:
      usernames = User.objects.order_by().filter(pk=user.id).values('id', 'username')

    context = {
      'theses': paged_documents,
      'pterm': projectterms,
      'cname': projectnames,
      'uname': usernames,
      'filter': True
    }
    return render(request, 'documents/index.html', context)


@login_required
def secondsearch(request):
  user = request.user
  if request.method == 'POST':
    class_name = request.POST['classname']
    personname_name = request.POST['personname']
    project_term = request.POST['projectterm1']

    theses = []
    if class_name and personname_name and project_term:
      theses = documents.objects.filter(Q(class_name__icontains=class_name), Q(documents_term__icontains=project_term), Q(admin_user=personname_name))


    paginator = Paginator(theses, 20)
    page = request.GET.get('page')
    paged_documents = paginator.get_page(page)

    projectterms = documents.objects.values('documents_term').annotate(dcount=Count('documents_term')).order_by()
    projectnames = documents.objects.values('class_name').annotate(dcount=Count('class_name')).order_by()
    if user.is_admin:
      usernames = User.objects.order_by().values('id', 'username')
    else:
      usernames = User.objects.order_by().filter(pk=user.id).values('id', 'username')

    context = {
      'theses': paged_documents,
      'pterm': projectterms,
      'cname': projectnames,
      'uname': usernames,
      'filter': True

    }
  return render(request, 'documents/index.html', context)

def readPDF(request, obj_id, file_name):
  splitters = ['.', '-', '/']
  titles = ['Öğr.Gör.', 'Öğr.Üyesi', 'Arş.Gör.Dr.', 'Arş.Gör.', 'Yrd.Doç.', 'Dr.Öğr.Üyesi', 'Dr.', 'Doç.Dr.', 'Doç.', 'Prof.Dr.', 'Prof.', 'Ord.Prof.Dr.']
  documents_name = ''
  title = ''
  term = ''
  summary = ''
  student_names = []
  student_numbers = []

  local_uplad_file_path = MEDIA_ROOT
  # tika.initVM()
  PDFfile = local_uplad_file_path + '/static/{}'.format(file_name).replace(" ","_")
  file_data = (parser.from_file(PDFfile))
  file_data_content = file_data['content']

  if not file_data_content:
    ocrmypdf.ocr(PDFfile, PDFfile, deskew=True,language="tur")
    file_data = (parser.from_file(PDFfile))
    file_data_content = file_data['content']

  txt_term = 'Tezin Savunulduğu Tarih:'
  txt_type1 = 'BİTİRME PROJESİ'
  txt_type2 = 'ARAŞTIRMA PROBLEMLERİ'

  txt_stu_no = 'Öğrenci No: '
  txt_stu_name = 'Adı Soyadı: '
  txt_summary = 'ÖZET '
  txt_keywords = 'Anahtar kelimeler: '
  txt_advisor = 'Danışman,'
  txt_lecturer = 'Jüri Üyesi,'

  isLessonType1 = isExist(file_data_content, txt_type1)
  isLessonType2 = isExist(file_data_content, txt_type2)
  if isLessonType1:
    documents_name = 'BİTİRME PROJESİ'
  elif isLessonType2:
    documents_name ='ARAŞTIRMA PROBLEMLERİ'
  else:
    documents_name = 'TESPİT EDİLEMEDİ'

  idx_term = findLine(file_data_content, txt_term)
  idx_term_dict = findIndexDict(file_data_content, txt_term)
  idx_stu_no = findIndexDict(file_data_content, txt_stu_no)
  idx_stu_name = findIndexDict(file_data_content, txt_stu_name)
  idx_summary = findIndexDict(file_data_content, txt_summary)
  idx_keywords = findLine(file_data_content, txt_keywords)
  idx_keywords_dict = findIndexDict(file_data_content, txt_keywords)
  # idx_advisor = findIndexDict(file_data_content, txt_advisor)
  # idx_lecturer = findIndexDict(file_data_content, txt_lecturer)

  # print(idx_term)
  # print(idx_stu_no)
  # print(idx_stu_name)
  # print(idx_summary)
  # print(idx_keywords)
  # print(idx_advisor)
  # print(idx_lecturer)


  for x in idx_stu_no:
    text = x['_line']
    num = ''
    for i in range(0, len(text)):
      if text[i].isdigit():
        num += text[i]
    student_numbers.append(num)
  print(student_numbers)

  for x in idx_stu_name:
    text = x['_line']
    n1 = len(txt_stu_name)
    n2 = len(text)
    name = text[n1:n2]
    student_names.append(name.strip())
  print(student_names)

  n2 = len(txt_term)
  n3 = len(idx_term)
  idx_term_date = idx_term[n2:n3].strip()
  for z in splitters:
    splitted_count = idx_term_date.split(z)
    if len(splitted_count) == 3:
      mount_value = splitted_count[1]
      year_value = splitted_count[2]
      year1 = int(year_value) - 1
      year2 = int(year_value) + 1
      if int(mount_value) < 8:
        term = str(year1) + '/' + year_value + ' BAHAR'
      else:
        term = year_value + '/' + str(year2) + ' GÜZ'

  print(documents_name)
  print(term)

  _inx1 = getLineNo(idx_summary, '10')
  _inx2 = getLineNo(idx_keywords_dict, '0')
  title_lines = setLines(file_data_content, _inx1-4, _inx1-1)
  title = setText(title_lines)
  summary_lines = setLines(file_data_content, _inx1+1, _inx2-1)
  summary = setText(summary_lines)

  _inx3 = getLineNo(idx_term_dict, '0')
  lecturer_data = []
  lecturer_data_object = []
  lecturer_data = setLines(file_data_content, _inx3-15, _inx3-1)
  lecturer_data_object = getLectureData(lecturer_data, titles)

  for obj in lecturer_data_object:
    print (obj.title, obj.name, obj.duty, sep=' - ')

  keywords_list = []
  keywords = []
  n4 = len(txt_keywords)
  n5 = len(idx_keywords)
  idx_keywords_list = idx_keywords[n4:n5].strip()
  keywords_list1 = idx_keywords_list.split(',')
  keywords_list2 = setLines(file_data_content, _inx2 + 1, _inx2 + 4)
  
  keywords = addToArray(keywords_list1)
  
  for i in keywords_list2:
    keywords_list3 = i.split(',')
    keywords_list3 = addToArray(keywords_list3)
    keywords = keywords + keywords_list3

  print(keywords)
  print(title)

  print(summary)
  try:
    t_obj = documents.objects.get(pk=obj_id)
    documents.objects.filter(pk=t_obj.id).update(class_name=documents_name, documents_title=title, documents_summary=summary, documents_term=term, )
    cnt = 0
    for std in student_names:
      if len(std) > 0 and cnt <= len(std):
        Student.objects.create(student_documents=t_obj, student_name=student_names[cnt], student_no= student_numbers[cnt],)
      cnt += 1

    for obj in lecturer_data_object:
      Jury.objects.create(jury_documents=t_obj, jury_title=obj.duty, lecturer_title= obj.title, lecturer_name=obj.name, is_consultant=isAdvisor(obj.duty),)

    cnt = 0
    for kyw in keywords:
      if len(kyw) > 0 and cnt <= len(kyw):
        Keyword.objects.create(keyword_documents=t_obj, keyword=keywords[cnt], )
      cnt += 1
  except Exception as e:
    if t_obj.id:
      t_obj.delete()

      print(e)
      return False

  print ('Ok')
  return True

def findLine(content, search_str):
  for line in content.splitlines():
    if search_str in line:
      return line

def findIndexDict(content, search_str):
  line_last = content.splitlines()
  inx_list = []
  for line_no, line in enumerate(line_last):
    if search_str in line:
      uni_line = line
      inx = line.index(search_str)
      if inx > -1:
        inx_line_dict = dict(_inx=inx, _line=uni_line, _line_no=line_no)
        inx_list.append(inx_line_dict)

  return inx_list

def setLines(content, num1, num2):
  line_last = content.splitlines()
  line_list = []
  for line_no, line in enumerate(line_last):
    if line_no >= num1 and line_no <= num2:
      if len(line) > 0 and not line.__contains__('vii'):
        line_list.append(line.strip())

  return line_list

def setText(lines):
  text = ''
  if len(lines) > 0:
    for line in lines:
      if len(line.strip()) > 5:
        text += line + ' '
  return text

def addToArray(textArray):
  new_array = []
  for text in textArray:
    if len(text) > 0 and not text.__contains__('vii'):
      new_array.append(text.strip().replace(".",""))

  return new_array


def isExist(content, search_str):
  for line in content.splitlines():
    if search_str in line:
      return True
  return False

def isAdvisor(text):
  if 'danışman' in text.lower():
    return True
  return False

def getLineNo(LineDict, _index):
  for x in LineDict:
    text = x['_line']
    if int(_index) > 0:
      if len(text)  < int(_index):
        inx = int(x['_line_no'])
    else:
      inx = int(x['_line_no'])
  return inx

def getLectureData(lecturer_data, titles):
  lecturer_list = []
  _title = ''
  _name = ''
  _duty = ''
  for data in lecturer_data:
    if len(data) > 0:
      if 'Danışman' not in data and 'Jüri' not in data:
        for title in titles:
          is_title_exists = False
          new_data = data.replace(' ', '')

          if new_data.lower().startswith(title.lower()):
            is_title_exists = True
            inx_char = new_data[len(title):len(title)+2]
            inx = data.index(inx_char)
            _title = title
            _name = data[int(inx): len(data)].strip()
            break
        if not is_title_exists:
          _title = '--'
          _name = data.strip()
      else:
        _data = data.split(', ')
        if len(_data) < 1:
          _duty = '--'
        else:
          _duty = _data[0]

    if len(_duty) > 0:
      lecturer_list.append(Lecturer(_title, _name, _duty))
      _duty = ''
      _name = ''
      _title = ''

  return lecturer_list
