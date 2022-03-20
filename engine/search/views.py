from email import message
from django.shortcuts import render
from matplotlib import image

from rest_framework import status
from sqlalchemy import null
from .serializers import DocumentSerializer, ResultSerializer
from .models import Documents, SearchHistory, Result, User
from .metadata import DocumentDTO, PageDTO, ImageDTO, ObjectDTO, ComplexEncoder, NumpyEncoder, Position
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
from PIL import Image, ImageDraw, ImageFilter
import pandas as pd
import argparse
import glob
import multiprocessing as mp
import os
import time
import cv2
import tqdm
import uuid
import shutil
import json
import shutil
import requests
from django.http import JsonResponse

from pdf2image import convert_from_path
from detectron2.config import get_cfg
from detectron2.data.detection_utils import read_image
from detectron2.utils.logger import setup_logger
from detectron2.data.detection_utils import convert_PIL_to_numpy

from .detection import ObjectDetection
from .predictor import VisualizationDemo
from detectron2.data import MetadataCatalog
from wsgiref.util import FileWrapper

WINDOW_NAME = "COCO detections"
logger = setup_logger()
MetadataCatalog.get("dla_val").thing_classes = ['text', 'title', 'list', 'table', 'figure']



@api_view(['GET'])
def getDocument(request,   *args, **kwargs):
    if request.method == 'GET':
        docID=kwargs.get('docID', None)
        docPath= "%s/%s.%s" % ("media/document",docID, "pdf")
        document = open(docPath, 'rb')
        response = HttpResponse(FileWrapper(document), content_type='application/pdf')
        return response

@api_view(['GET'])
def getResultDocument(request,   *args, **kwargs):
    if request.method == 'GET':
        docID=kwargs.get('docID', None)
        resultDocID=kwargs.get('resultDocID', None)
        docPath= "%s/%s/%s.%s" % ("media/result",docID,resultDocID, "pdf")
        document = open(docPath, 'rb')
        response = HttpResponse(FileWrapper(document), content_type='application/pdf')
        return response

@api_view(['POST'])
def search(request):
  if request.method == 'POST':

    query = """index=metadata "pages{}.images{}.objects{}.name"=person"""
    # ----------------- GET SEARCH SPLUNK ------------------------------
    url = "https://localhost:8089/services/search/jobs/export"
    params = {'search': f'search {query}', 'output_mode': 'csv'}
    r = requests.get(url, params=params, auth=('dedicoder', 'asdfgwer1'), verify=False)
    data = r.content.decode('utf-8').replace('""', '"')
    data = data.split("\n")
    js = ''' { "rows" : [ '''
    for x in range(1, len(data)):
        spl = data[x].split(",")
        for y in range(7, len(spl)):
            if (y == 7):
                spl[y] = spl[y][1:]
            elif (y == len(spl) - 1):
                spl[y] = spl[y][1:-1]
            js = js + spl[y] + ","
    js = js[0:-1]
    js = js + "]}"

    #print(js)
    responseJSon = json.loads(js)
    print("-------------")
    print(responseJSon['rows'][0]['size'])


    serializer = DocumentSerializer(data=request.data)

    projectPath = os.path.abspath(os.path.dirname(__name__))
    documentDir = "media/document"
    if not os.path.exists(os.path.join(projectPath, documentDir)):
      os.makedirs(os.path.join(projectPath, documentDir))
    
    query = request.POST['query']
    username = request.POST['user']
    docID = request.POST.get('docID')

    if not docID:
        file = request.FILES['file'].read()
        fileName= request.POST['filename']
        existingPath = request.POST['existingPath']
        end = request.POST['end']
        nextSlice = request.POST['nextSlice']
    
    if docID:
      searchHistory = init(docID, query)
      if searchHistory:
        resultDocUrl = "%s://%s/result/%s/%s" % (request.scheme, request.get_host(),docID, searchHistory.resultDocID)
        message = "Arama Tamamlandı. " + searchHistory.resultMessage
        res = JsonResponse({'message':message, 'docID': docID,'resultDocID':searchHistory.resultDocID, 'resultDocUrl': resultDocUrl, 'resultTotalPage': searchHistory.resultTotalPage, 'resultPageList': searchHistory.resultPageList})
      else:
        res = JsonResponse({'message':'Arama Tamamlandı. Sonuç Bulunamadı.',})
      return res

    #  return res
    if file=="" or fileName=="" or existingPath=="" or end=="" or nextSlice=="":
        res = JsonResponse({'message':'Hata Oluştu.'})
        return res
    else:
        if existingPath == 'null':
            document = Documents()
            if username != "null" and username != 'AnonymousUser':
                user = User.objects.get(username=username)
                document.user = user
            document.docPath = file
            document.eof = end
            document.name = fileName
            path = "%s/%s.%s" % ("media/document",document.docID, fileName.split('.')[-1])
            document.docPath = path
            with open(path, 'wb+') as destination: 
                destination.write(file)
            document.save()
            if int(end):
                res = JsonResponse({'message':'Yükleme Tamamlandı. İşleniyor...', 'docID':document.docID,'existingPath': path})
            else:
                res = JsonResponse({'existingPath': path})
            return res

        else:
            document = Documents.objects.get(docPath=existingPath)
            if document.name == fileName:
                if not document.eof:
                    with open(existingPath, 'ab+') as destination: 
                        destination.write(file)
                    if int(end):
                        document.eof = int(end)
                        document.save()
                        res = JsonResponse({'message':'Yükleme Tamamlandı. İşleniyor...', 'docID':document.docID,'existingPath':document.docPath})
                    else:
                        res = JsonResponse({'existingPath':document.docPath})    
                    return res
                else:
                    res = JsonResponse({'message':'EOF. Geçersiz İstek'})
                    return res
            else:
                res = JsonResponse({'message':'Dosya Bulunamadı'})
                return res
  return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def searchById(request):
    if request.method == 'POST':
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            docID = request.data['docID']
            query = request.data['query']
            result = init(docID, query)
            if result:
                serializer = ResultSerializer(result)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def init(docID, query):
    document = Documents.objects.get(Q(docID=docID))
    if document:
        # searchHistory = SearchHistory.objects.filter(Q(document=document)).order_by('pk').last()
        docPath = document.docPath
        metadataId = document.metadataID
        if not metadataId:
            metadataId, metadataPath = find(docID,docPath)
            document.metadataID = metadataId
            document.metadataPath = metadataPath
            document.save()
        result =  filter(docID,metadataId, query)
        if result:
            return SearchHistory.objects.create(document=document, query=query, resultDocID=result.docID, resultDocPath=result.docPath, resultTotalObject=result.totalObject, resultTotalImage=result.totalImage, resultTotalPage=result.totalPage, resultPageList=result.pageList, resultMessage=result.message)
        else:
            SearchHistory.objects.create(document=document, query=query, resultMessage="Sonuç Bulunamadı")
    return None

def find(docID,docPath):
    mp.set_start_method("spawn", force=True)  
    cfg_DLA_Model = setup_cfg_DLA_Model()
    demo = VisualizationDemo(cfg_DLA_Model)
    outputDir = "%s/%s" % ("media/output",docID)
    resultDir = "%s/%s" % ("media/result",docID)
    inputs = [docPath]
    if len(inputs) == 1:
        inputs = glob.glob(os.path.expanduser(inputs[0]))
        assert inputs, "The input path(s) was not found"

    for path in tqdm.tqdm(inputs, disable=not outputDir):
        prepareFolderStructure(outputDir)
        prepareResultFolderStructure(resultDir)
        document = createDocumentObject(docID, path) 
        imagePages = convertPdfToPngPerPage(path)
        for i in range(len(imagePages)):
            page_id=uuid.uuid4().hex
            pageNumber= i+1
            page = PageDTO(page_id,pageNumber)
            page_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"pages",page_id, "jpg")
            imagePages[i].save(page_path)
            pageImgBGR= convert_PIL_to_numpy(imagePages[i], format="BGR")
            findImagesInPage(page, pageImgBGR, imagePages[i], docID, pageNumber, demo)
            document.addPage(page)

    json_data = json.dumps(document.reprJSON(), cls=NumpyEncoder)
    metadata_id=uuid.uuid4().hex
    metadataPath= "%s/%s.%s" % ("media/metadata",metadata_id, "json")
    """ #------------ Upload metadata Splunk --------------------
    upload_json_data = {"event": json.dumps(document.reprJSON(), cls=NumpyEncoder)}
    upload_json_data = json.dumps(upload_json_data, cls=NumpyEncoder)
    url = "https://localhost:8088/services/collector/event"
    headers = {"Authorization": "Splunk 6e305e21-1550-48d6-8f73-a2b5a744ebbc"}
    r = requests.post(url, data=upload_json_data, headers=headers, verify=False)
    print(r.content)
    """
    with open(metadataPath, 'w') as f:
        f.write(json_data)
    return metadata_id, metadataPath

def findImagesInPage(page, pageImgBGR, pageImg, docID, pageNumber, demo):
    start_time = time.time()
    predictions = demo.run_on_image(pageImgBGR)
    predictions = predictions["instances"].to(demo.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None

    #logger.info("{}: page {} :  detected {} instances in {:.2f}s".format(docID,pageNumber, len(predictions["instances"]), time.time() - start_time))
    # logger.info(
    #     "{} , page {} :  detected {} instances in {:.2f}s".format(
    #         docID,pageNumber, len(predictions["instances"]), time.time() - start_time
    #     )
    # )
    
    for index, item in enumerate(classes):
        if item == 4:
            box = list(boxes)[index].detach().cpu().numpy()
            crop_img = crop_object(pageImg, box)
            img_id=uuid.uuid4().hex
            img_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"images",img_id, "jpg")
            crop_img.save(img_path)
            position= createPositionObject(boxes.tensor[index].numpy())
            image = ImageDTO(img_id,position,scores[index].numpy(),crop_img.width,crop_img.height)
            findObjectsInImage(image,img_path)
            page.addImage(image)

def findObjectsInImage(image,imgPath):
    cfg_OD_Model = setup_cfg_OD_Model()
    objectDetection = ObjectDetection(cfg_OD_Model)
    predictions, className= objectDetection.detect(imgPath)
    predictions = predictions["instances"].to(objectDetection.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None
    
    for index, item in enumerate(classes):
        obj_id=uuid.uuid4().hex
        position= createPositionObject(boxes.tensor[index].numpy())
        object=ObjectDTO(obj_id,className[item],position,scores[index].numpy())
        image.addObject(object)


def filter(docID,metadataId, query):
    tempOutputDir = "%s/%s" % ("media/tempOutput",docID)
    prepareFolderStructure(tempOutputDir)
    if isinstance(metadataId, uuid.UUID):
        metadataId = metadataId.hex
    metadataPath= "%s/%s.%s" % ("media/metadata",metadataId, "json")
    with open(metadataPath) as data_file:    
        metadata = json.load(data_file)  

    df = pd.json_normalize(
    metadata, 
    record_path =['pages', 'images', 'objects'],  
    meta=[
        ['pages', 'id'],
        ['pages', 'pageNumber'],
        ['pages', 'images', 'id'], 
        ['pages', 'images', 'position']
    ],
    record_prefix='pages.images.objects.')#potted plant
    df.query('`pages.images.objects.name` == "{}"'.format(query),inplace = True)
    if df.empty:
        return None
    df = df.reset_index()
    for index, row in df.iterrows():
        objectPosition=[row['pages.images.objects.position.x1'],row['pages.images.objects.position.x2'],row['pages.images.objects.position.y1'],row['pages.images.objects.position.y2']]
        drawBox(docID,row['pages.images.id'], objectPosition)
        imagePosition = [row['pages.images.position']['x1'],row['pages.images.position']['x2'],row['pages.images.position']['y1'],row['pages.images.position']['y2']]
        addNewImageToPage(docID,row['pages.id'], row['pages.images.id'],imagePosition)
    
    return createResultDocument(docID, metadata, len(df.index), len(df.groupby(['pages.images.id'])))

def drawBox(docID, imgId, box):
    imgPath = "%s/%s/%s/%s.%s" % ("media/output",docID,"images",imgId, "jpg")
    outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images",imgId, "jpg")
    #color = list(np.random.random(size=3) * 256)
    #rgb = (random.random(), random.random(), random.random())

    if os.path.isfile(outputImgPath):
        imgPath = outputImgPath
        
    image = cv2.imread(imgPath)
    start_point = (int(box[0]), int(box[1]))
    end_point = (int(box[2]), int(box[3]))
    colors = [(255, 0, 0),(0, 255, 0),(0, 0, 255)]
    thickness = 2
    image = cv2.rectangle(image, start_point, end_point, colors[random.randint(0,2)], thickness)
    cv2.imwrite(outputImgPath, image)


def createResultDocument(docID, data, totalObject, totalImage):
    df = pd.json_normalize(data, record_path =['pages'])
    resultDocID= uuid.uuid4().hex
    resultDocPath = "%s/%s/%s.%s" % ("media/result",docID,resultDocID, "pdf")
    pages=[]
    totalPage=0
    pageList=""
    for index, row in df.iterrows():
        pagePath = "%s/%s/%s/%s.%s" % ("media/output",docID,"pages",row['id'], "jpg")
        tempPagePath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"pages",row['id'], "jpg")
        if os.path.isfile(tempPagePath):
            pagePath = tempPagePath
            totalPage+= 1
            if not pageList:
                pageList = row['pageNumber']
            else:
                pageList = "%s, %s" % (pageList, row['pageNumber'])
        pages.append(Image.open(pagePath))
          
    pages[0].save(resultDocPath, "PDF" ,resolution=100.0, save_all=True, append_images=pages[1:])
    message = "%s Sayfada Bulunan %s Resimde %s Nesne İşaretlendi." % (totalPage, totalImage, totalObject)
    result = Result(resultDocID, resultDocPath, totalObject, totalImage, totalPage, pageList, message)
    return result

def addNewImageToPage(docID,pageID, imageID, position):
    pagePath = "%s/%s/%s/%s.%s" % ("media/output",docID,"pages",pageID, "jpg")
    imagePath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images",imageID, "jpg")
    page = Image.open(pagePath)
    image = Image.open(imagePath)
    tempPage = page.copy()
    tempPage.paste(image, (int(position[0]), int(position[1]), int(position[2]), int(position[3])))
    outputPagePath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"pages",pageID, "jpg")
    tempPage.save(outputPagePath, quality=100)

def createPositionObject(position):
    return Position(position[0],position[1],position[2],position[3])

def crop_object(image, box):
  x_top_left = box[0]
  y_top_left = box[1]
  x_bottom_right = box[2]
  y_bottom_right = box[3]
  x_center = (x_top_left + x_bottom_right) / 2
  y_center = (y_top_left + y_bottom_right) / 2
  crop_img = image.crop((int(x_top_left), int(y_top_left), int(x_bottom_right), int(y_bottom_right)))
  return crop_img

def setup_cfg_DLA_Model():
    cfg = get_cfg()
    cfg.merge_from_file("configs/DLA_mask_rcnn_X_101_32x8d_FPN_3x.yaml")
    cfg.merge_from_list(['MODEL.WEIGHTS', 'models/model_final_trimmed.pth', 'MODEL.DEVICE', 'cpu'])
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
    cfg.freeze()
    return cfg

def setup_cfg_OD_Model():
    cfg = get_cfg()
    cfg.merge_from_file("configs/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.WEIGHTS = "models/model_final_68b088.pkl"
    cfg.MODEL.DEVICE = "cpu"
    return cfg

def convertPdfToPngPerPage(pdfPath):
    images = convert_from_path(pdfPath)
    return images

def createDocumentObject(docID, path):
    file = open(path, 'rb')
    parser = PDFParser(file)
    doc = PDFDocument(parser)
    totalPages = resolve1(doc.catalog['Pages'])['Count']
    size=os.path.getsize(path)
    docInfo=doc.info[0]
    creator=producer=title=keywords=creationDate=""
    if 'Creator' in docInfo:
        creator= ['Creator'].decode("utf-8") 
    if 'Producer' in docInfo:
        producer=doc.info[0]['Producer'].decode("utf-8")
    if 'Title' in docInfo:
        title=doc.info[0]['Title'].decode("utf-8")
    if 'Keywords' in docInfo:
        keywords= doc.info[0]['Keywords'].decode("utf-8")
    if 'CreationDate' in docInfo:
        creationDate=doc.info[0]['CreationDate'].decode("utf-8")
    document = DocumentDTO(docID,size,totalPages,creator,keywords,producer,title,creationDate)
    return document

def prepareFolderStructure(outputDir):
    projectPath = os.path.abspath(os.path.dirname(__name__))
    if os.path.exists(os.path.join(projectPath, outputDir)):
        shutil.rmtree(os.path.join(projectPath, outputDir))
    pagesPath = "%s/%s" % (outputDir,"pages")
    imagesPath = "%s/%s" % (outputDir,"images")
    os.makedirs(os.path.join(projectPath, pagesPath))
    os.makedirs(os.path.join(projectPath, imagesPath))

def prepareResultFolderStructure(resultDir):
    projectPath = os.path.abspath(os.path.dirname(__name__))
    if os.path.exists(os.path.join(projectPath, resultDir)):
        shutil.rmtree(os.path.join(projectPath, resultDir))
    os.makedirs(os.path.join(projectPath, resultDir))