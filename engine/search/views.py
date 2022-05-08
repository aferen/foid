from rest_framework import status
from .serializers import DocumentSerializer, ResultSerializer
from .models import Documents, SearchHistory, Result, User, Objects
from .metadata import DocumentDTO, PageDTO, ImageDTO, ObjectDTO,NumpyEncoder, Position
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import resolve1
import logging
import re
from PIL import Image, ImageDraw
import pandas as pd
import glob
import multiprocessing as mp
import os
import time
import tqdm
import uuid
import shutil
import json
import shutil
import numpy as np
from django.http import JsonResponse
from pdf2image import convert_from_path
from detectron2.config import get_cfg
from detectron2.data.detection_utils import convert_PIL_to_numpy
from .detection import Detection
from wsgiref.util import FileWrapper
#WINDOW_NAME = "COCO detections"
#logger = setup_logger()
#MetadataCatalog.get("dla_val").thing_classes = ['text', 'title', 'list', 'table', 'figure']

imageDetection = {}
objectDetection = {}
chartDetection = {}
objectClassName = {}
logger = logging.getLogger(__name__)

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
    serializer = DocumentSerializer(data=request.data)
    projectPath = os.path.abspath(os.path.dirname(__name__))
    documentDir = "media/document"
    if not os.path.exists(os.path.join(projectPath, documentDir)):
        os.makedirs(os.path.join(projectPath, documentDir))
    
    query = request.POST['query']
    query = query.replace(" ", "").replace('İ', 'i').lower()
    username = request.POST['user']
    docID = request.POST.get('docID')
    advancedSearch = request.POST.get('advancedSearch')
    if advancedSearch == "true":
        advancedSearch = isAdvancedSearch(query)
    else:
        advancedSearch = False
    validate = validateQuery(query,advancedSearch)
    if not validate:
        res = JsonResponse({'message':'Geçersiz Arama Yapıldı.',})
        return res

    if not docID:
        file = request.FILES['file'].read()
        fileName= request.POST['filename']
        existingPath = request.POST['existingPath']
        end = request.POST['end']
        nextSlice = request.POST['nextSlice']
    
    if docID:
        try:
            searchHistory, metadataID,errorMessage = init(docID, query,advancedSearch)
            if not isinstance(metadataID, str):
                metadataID = metadataID.hex
            resultReport = getResultReport(metadataID)
            if searchHistory == "Invalid":
                res = JsonResponse({'message':errorMessage,'resultReport': resultReport})
            elif searchHistory:
                resultDocUrl = "%s://%s/result/%s/%s" % (request.scheme, request.get_host(),docID, searchHistory.resultDocID)
                message = "Arama Tamamlandı. " + searchHistory.resultMessage
                res = JsonResponse({'message':message, 'docID': docID,'resultDocID':searchHistory.resultDocID, 'resultDocUrl': resultDocUrl, 'resultTotalPage': searchHistory.resultTotalPage, 'resultPageList': searchHistory.resultPageList, 'resultReport': resultReport})
            else:
                res = JsonResponse({'message':'Arama Tamamlandı. Sonuç Bulunamadı.','resultReport': resultReport})
        except Exception as e:
            logger.exception(e)
            res = JsonResponse({'message':'Hata Oluştu.',})
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
            advancedSearch = request.POST.get('advancedSearch')
            result, metadataID = init(docID, query, advancedSearch)
            if result:
                serializer = ResultSerializer(result)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def getResultReport(metadataID):
    metadataPath= "%s/%s.%s" % ("media/metadata",metadataID, "json")

    with open(metadataPath) as data_file:
        data = json.load(data_file)

    df = pd.json_normalize(
        data,
        record_path =['pages', 'images', 'objects']
    )

    df.loc[:, 'temp1'] = 1
    df.loc[df.score < 0.5, "score"] = 0.5
    df = df.round(1)
    df = df.pivot_table('temp1', ['name'], 'score', aggfunc=np.sum)
    df["count"] = df.sum(axis=1)
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    df.reset_index(inplace=True)
    
    if 0.5 not in df:
        df.loc[:, 0.5] = 0
    if 0.6 not in df:
        df.loc[:, 0.6] = 0
    if 0.7 not in df:
        df.loc[:, 0.7] = 0
    if 0.8 not in df:
        df.loc[:, 0.8] = 0
    if 0.9 not in df:
        df.loc[:, 0.9] = 0
    if 1.0 not in df:
        df.loc[:, 1.0] = 0

    df = df.replace(np.nan, 0)
    df.loc[:, 'color'] = ''
    for index, row in df.iterrows():
        df["color"][index]= objectClassName.get(nameTR=row['name'])["color"]
    columnsTitles = ['name', 'color', 'count', 0.5,0.6,0.7,0.8,0.9,1.0]
    df = df.reindex(columns=columnsTitles)
    return df.to_json(orient='records',force_ascii=False) 

def isAdvancedSearch(query):
    if ("&" not in query and "|" not in query and "!" not in query and "(" not in query and ")" not in query):
        return False
    return True

def validateQuery(query, advancedSearch):
    if not advancedSearch:
        if query.isalpha():
            return True
    else: 
        if not any(char.isdigit() for char in query) and parenthesesCheck(query) and  query[0] != "|" and query[0] != "&" and query[len(query)-1] != "|" and query[len(query)-1] != "&" and query[len(query)-1] != "!":
            return True
    return False

def parenthesesCheck(query):
    stack = []
    open_list = ["("]
    close_list = [")"]
    for i in query:
        if i in open_list:
            stack.append(i)
        elif i in close_list:
            pos = close_list.index(i)
            if ((len(stack) > 0) and
                (open_list[pos] == stack[len(stack)-1])):
                stack.pop()
            else:
                return False
    if len(stack) == 0:
        return True
    else:
        return False

def init(docID, query, advancedSearch):
    global objectClassName
    document = Documents.objects.get(Q(docID=docID))
    if document:
        objectClassName = Objects.objects.all().values('nameTR', 'color')
                
        
        # searchHistory = SearchHistory.objects.filter(Q(document=document)).order_by('pk').last()
        docPath = document.docPath
        metadataId = document.metadataID

        if not metadataId:
            logger.info('Document is analyzed for the first time. Document ID: %s Query: %s', docID,query)
            metadataId, metadataPath = find(docID,docPath)
            document.metadataID = metadataId
            document.metadataPath = metadataPath
            document.save()
        else:
            logger.info('Document has been analysed. Document ID: %s Metadata ID: %s Query: %s', docID, metadataId, query)

        for i in range(len(objectClassName)):
            objectClassName[i]["nameTR"] = objectClassName[i]["nameTR"].replace(" ", "")

        if advancedSearch:
            query = query.replace(" ", "")
            querySentences, wordList, errormessage = createQuerySentences(query)
            if errormessage:
                SearchHistory.objects.create(document=document, query=query, resultMessage=errormessage,isAdvancedSearch=advancedSearch)
                return "Invalid", metadataId,errormessage
            else:
                result =  advancedfilter(docID,metadataId, querySentences, wordList)
        else:
            #obj = objectClassName.filter(nameTR=query1)
            obj = [x for x in objectClassName if x['nameTR'] == query]
            if not obj:
                errormessage = "%s nesnesi için arama yapılamamaktadır." % (query)
                return "Invalid", metadataId,errormessage
            result =  filter(docID,metadataId, query)

        if result == "Invalid":
            SearchHistory.objects.create(document=document, query=query, resultMessage="Geçersiz Arama Yapıldı",isAdvancedSearch=advancedSearch)
            errorMessage = 'Geçersiz Arama Yapıldı.'
            return "Invalid",metadataId,errorMessage
        elif result:
            return SearchHistory.objects.create(document=document, query=query, resultDocID=result.docID, resultDocPath=result.docPath, resultTotalObject=result.totalObject, resultTotalImage=result.totalImage, resultTotalPage=result.totalPage, resultPageList=result.pageList, resultMessage=result.message, isAdvancedSearch=advancedSearch), metadataId,None
        else:
            SearchHistory.objects.create(document=document, query=query, resultMessage="Sonuç Bulunamadı",isAdvancedSearch=advancedSearch)
    
    return None, metadataId, None

def find(docID,docPath):
    start_time = time.time()
    global imageDetection
    global objectDetection
    global chartDetection
    imageDetection = Detection(setup_cfg_DLA_Model())
    objectDetection = Detection(setup_cfg_OD_Model())
    chartDetection = Detection(setup_cfg_CHT_Model())
    mp.set_start_method("spawn", force=True)  
    outputDir = "%s/%s" % ("media/output",docID)
    resultDir = "%s/%s" % ("media/result",docID)
    metadataDir = "media/metadata"
    inputs = [docPath]
    if len(inputs) == 1:
        inputs = glob.glob(os.path.expanduser(inputs[0]))
        assert inputs, "The input path(s) was not found"

    for path in tqdm.tqdm(inputs, disable=not outputDir):
        prepareFolderStructure(outputDir)
        prepareResultFolderStructure(resultDir)
        metadataFolderStructure(metadataDir)
        document = createDocumentObject(docID, path) 
        imagePages = convertPdfToPngPerPage(path)
        for i in range(len(imagePages)):
            page_id=uuid.uuid4().hex
            pageNumber= i+1
            page = PageDTO(page_id,pageNumber)
            page_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"pages",page_id, "jpg")
            imagePages[i].save(page_path)
            pageImgBGR= convert_PIL_to_numpy(imagePages[i], format="BGR")
            findImagesInPage(page, pageImgBGR, imagePages[i], docID, pageNumber)
            document.addPage(page)

    json_data = json.dumps(document.reprJSON(), cls=NumpyEncoder)
    metadata_id=uuid.uuid4().hex
    metadataPath= "%s/%s.%s" % (metadataDir ,metadata_id, "json")
    with open(metadataPath, 'w') as f:
        f.write(json_data)
    logger.info("Metadata file created: Metadata ID: %s", metadata_id)
    logger.info("Document analysis completed in {:.2f}s".format(time.time() - start_time))
    return metadata_id, metadataPath

def findImagesInPage(page, pageImgBGR, pageImg, docID, pageNumber):
    start_time = time.time()
    predictions = imageDetection.detectImagesInPage(pageImgBGR)

    predictions = predictions["instances"].to(imageDetection.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None
    arr = np.array(classes)
    logger.info(
        "(Page number: {}) detected {} images in {:.2f}s".format(
            pageNumber, len(arr[arr == 4]), time.time() - start_time
        )
    )
    cnt=0
    for index, item in enumerate(classes):
        if item == 4:
            cnt = cnt+1
            box = list(boxes)[index].detach().cpu().numpy()
            crop_img = crop_object(pageImg, box)
            img_id=uuid.uuid4().hex
            img_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"images",img_id, "jpg")
            crop_img.save(img_path)
            position= createPositionObject(boxes.tensor[index].numpy())
            image = ImageDTO(img_id,position,scores[index].numpy(),crop_img.width,crop_img.height)
            objectCount = findObjectsInImage(image,img_path,pageNumber, cnt)
            #if objectCount == 0:
            findChartInImage(image,img_path,pageNumber, cnt)
            page.addImage(image)

def findObjectsInImage(image,imgPath,pageNumber, imageNumber):
    start_time = time.time()
    predictions= objectDetection.detectObjectsInImage(imgPath)
    objectCount = len(predictions["instances"])
    logger.info(
        "(Page number: {}) ({}. Image) detected {} objects in {:.2f}s".format(
            pageNumber, imageNumber, objectCount, time.time() - start_time
        )
    )
    predictions = predictions["instances"].to(objectDetection.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None
  
    for index, item in enumerate(classes):
        obj_id=uuid.uuid4().hex
        position= createPositionObject(boxes.tensor[index].numpy())
        object=ObjectDTO(obj_id,objectClassName[item]['nameTR'],position,scores[index].numpy())
        image.addObject(object)

    return objectCount

def findChartInImage(image,imgPath,pageNumber, imageNumber):
    start_time = time.time()
    predictions= chartDetection.detectChartInImage(imgPath)
    logger.info(
        "(Page number: {}) ({}. Image) detected {} charts in {:.2f}s".format(
            pageNumber, imageNumber, len(predictions["instances"]), time.time() - start_time
        )
    )
    predictions = predictions["instances"].to(objectDetection.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None
  
    for index, item in enumerate(classes):
        obj_id=uuid.uuid4().hex
        position= createPositionObject(boxes.tensor[index].numpy())
        obj = objectClassName.get(objectID=item+500-1)
        object=ObjectDTO(obj_id,obj['nameTR'],position,scores[index].numpy())
        image.addObject(object)


def createQuerySentences(query):
    queries = []
    queryTemp=query
    querySentences=[]
    allWordList=[]
    while ")|" in query:
        print(query)
        index1 = query.index(')|')+1
        print(index1)
        if len(query[:index1]) > 1:
            queries.append(query[:index1])
        query = query[index1:]
    
    while "|(" in query:
        print(query)
        index1 = query.index('|(')+1
        print(index1)
        if len(query[:index1]) > 1:
            queries.append(query[:index1])
        query = query[index1:]

    queries.append(query) 
    print(queries)
    for i in range(len(queries)):
        if queries[i][0] == "|":
            queries[i] = queries[i][1:]
        if queries[i][len(queries[i])-1] == "|":
            queries[i] = queries[i][:len(queries[i])-1]

    print(queries)
    for k in range(len(queries)):
        words = re.split('&|\|',queries[k])
        lastCon=""
        wordList=[]
        for i in range(0,len(words)):
            word=words[i].replace("(","").replace(")","")
            if word not in wordList:
                wordList.append(word)
                if word not in allWordList:
                    allWordList.append(word)
                index = queries[k].index(word)
                if "!" in word:
                    obj = [x for x in objectClassName if x['nameTR'] == word[1:]]
                    if not obj:
                        message = "%s nesnesi için arama yapılamamaktadır." % (word[1:])
                        return None, None, message
                else:
                    obj = [x for x in objectClassName if x['nameTR'] == word]
                    if not obj:
                        message = "%s nesnesi için arama yapılamamaktadır." % (word)
                        return None, None, message
                #obj = objectClassName.filter(nameTR=word)

                
                if "!" in word:
                    con=word[1:]+"!="+word[1:]
                    if index == 0:
                        if queries[k][len(word)-1] == "&":
                            lastCon=" and (%s != %s)%s" % (word[1:],word[1:],lastCon)
                        else:
                            lastCon=" or (%s != %s)%s" % (word[1:],word[1:],lastCon)
                    else:
                        if queries[k][index-1] == "&" or queries[k][index+len(word)] == "&":
                            lastCon=" and (%s != %s)%s" % (word[1:],word[1:],lastCon)
                        else:
                            lastCon=" or (%s != %s)%s" % (word[1:],word[1:],lastCon)                        
                else:
                    con = word + "==" + word
                    if lastCon[-1:] == ")" or not lastCon:
                        lastCon = "%s and (%s == 1" % (lastCon, word)
                    else:
                        lastCon = "%s or %s == 1" % (lastCon, word)
                queries[k] = queries[k].replace(word,con)

        queries[k] = queries[k].replace("&"," and ").replace("|"," or ")
        queries[k]="(%s)" % (queries[k])
        print(queries[k])
        if lastCon[-1:] != ")":
            lastCon="%s)" % (lastCon)
        querySentence=queries[k]+lastCon
        querySentences.append(querySentence)
    print(querySentences)

 
    # if lastCon[-1:] != ")":
    #     lastCon="%s)" % (lastCon)
    # querySentence=query+lastCon
    # print(querySentence)
    #querySentence="((boat==boat and person==person) or (clock==clock)) and ((boat == 1 and person == 0) or (boat == 0 and person == 1) or clock == 1)"
    return querySentences, allWordList, None

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
    record_prefix='pages.images.objects.')
    df['pages.images.objects.objectName'] = df['pages.images.objects.name']
    df['pages.images.objects.name'].replace('\s+', '', regex=True, inplace=True)
    df.query('`pages.images.objects.name` == "{}"'.format(query),inplace = True)
    if df.empty:
        return None
    df = df.reset_index()
    newImage = True
    for index, row in df.iterrows():
        imgID = row['pages.images.id']
        outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
        if newImage:
            imgPath = "%s/%s/%s/%s.%s" % ("media/output",docID,"images", imgID, "jpg")
            #image = cv2.imread(imgPath)
            image = Image.open(imgPath)
        objectPosition=[row['pages.images.objects.position.x1'],row['pages.images.objects.position.x2'],row['pages.images.objects.position.y1'],row['pages.images.objects.position.y2']]
        #obj = objectClassName.get(nameTR=row['pages.images.objects.objectName'])
        obj = [x for x in objectClassName if x['nameTR'] == row['pages.images.objects.name']][0]
        color = obj["color"]
        image = drawBox(image, objectPosition,color)
        if (index+1==len(df)):
            outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
            #cv2.imwrite(outputImgPath, image)
            image.save(outputImgPath)
            imagePosition = [row['pages.images.position']['x1'],row['pages.images.position']['x2'],row['pages.images.position']['y1'],row['pages.images.position']['y2']]
            addNewImageToPage(docID,row['pages.id'], imgID,imagePosition)     
        elif (df['pages.images.id'][index+1] != imgID):
            outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
            #cv2.imwrite(outputImgPath, image)
            image.save(outputImgPath)            
            imagePosition = [row['pages.images.position']['x1'],row['pages.images.position']['x2'],row['pages.images.position']['y1'],row['pages.images.position']['y2']]
            addNewImageToPage(docID,row['pages.id'], imgID,imagePosition)
            newImage = True
        else:
            newImage = False
    
    return createResultDocument(docID, metadata, len(df.index), len(df.groupby(['pages.images.id'])))


def advancedfilter(docID,metadataId, querySentences, wordList):
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
        'id',
        ['pages', 'id'],
        ['pages', 'pageNumber'],
        ['pages', 'images', 'id'], 
        ['pages', 'images', 'position']
    ],
    record_prefix='pages.images.objects.')

    df.loc[:, 'temp1'] = 1
    #df.loc[:, 'temp2'] = ''
    df['pages.images.objects.objectName'] = df['pages.images.objects.name'].replace(" ","")
    df = df.astype({"pages.images.position": str})
    df2 = df.pivot_table('temp1', ['id','pages.id', 'pages.pageNumber', 'pages.images.id', 'pages.images.position','pages.images.objects.position.x1','pages.images.objects.position.x2','pages.images.objects.position.y1','pages.images.objects.position.y2', 'pages.images.objects.objectName'], 'pages.images.objects.name')
    df2.columns = [i.replace(" ","") for i in df2.columns]
    df2.loc[:, 'temp2'] = None
    df2.reset_index(inplace=True)
    for i in range(0,len(wordList)): 
        word=wordList[i].replace("!","")
        # print(word)
        # print(df2.columns.tolist())
        if word not in df2.columns.tolist():
            for j in range(len(querySentences)):
                querySentences[j] = querySentences[j].replace(word, "temp2")

    #querySentences[0] = querySentences[0].replace("saat", "temp2")


    for index in range(10,len(df2.columns)-1):
        df4 = df2.groupby('pages.images.id')[df2.columns[index]].apply(set).to_dict()
        def control(row):
            match = row[df2.columns[index]] in df4[row['pages.images.id']]
            if match:
                df2.loc[((df2[df2.columns[3]] == row[3]) & (np.isnan(df2[df2.columns[index]]))), df2.columns[index]] = 0
            return match
            # return match2 or (match1 and (row['Num1'] in range(5, 13)))
        df2.apply(control, axis=1).astype(int)
    try:
        #querySentence="((tekne==1 and kişi==0) or (tekne==0 and kişi==1)) and şemsiye==şemsiye"
        #querySentence="((tekne==tekne and kişi==kişi) or (saat==1)) and (tekne == 1 or kişi == 1 or saat == 1)"
        df3=df2[0:0]
        for i in range(len(querySentences)):
            df3 = df3.append(df2.query(querySentences[i]),ignore_index=True)
        df3.drop_duplicates()
    except:
        logger.exception("Invalid query sentence")
        return "Invalid"
    if df3.empty:
        return None
    df3 = df3.reset_index()
    newImage = True 
    for index, row in df3.iterrows():
        imgID = row['pages.images.id']
        outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
        if newImage:
            imgPath = "%s/%s/%s/%s.%s" % ("media/output",docID,"images", imgID, "jpg")
            if os.path.isfile(outputImgPath):
                imgPath = outputImgPath
            #image = cv2.imread(imgPath)
            image = Image.open(imgPath)
        objectPosition=[row['pages.images.objects.position.x1'],row['pages.images.objects.position.x2'],row['pages.images.objects.position.y1'],row['pages.images.objects.position.y2']]
        obj = objectClassName.get(nameTR=row['pages.images.objects.objectName'])
        color = obj["color"]
        image = drawBox(image, objectPosition,color)
        if (index+1==len(df3)):
            outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
            #cv2.imwrite(outputImgPath, image)
            image.save(outputImgPath)
            imagePositionObject = json.loads(row['pages.images.position'].replace("'","\""))
            imagePosition = [imagePositionObject['x1'],imagePositionObject['x2'],imagePositionObject['y1'],imagePositionObject['y2']]
            addNewImageToPage(docID,row['pages.id'], imgID,imagePosition)     
        elif (df3['pages.images.id'][index+1] != imgID):
            outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images", imgID, "jpg")
            #cv2.imwrite(outputImgPath, image)
            image.save(outputImgPath)
            imagePositionObject = json.loads(row['pages.images.position'].replace("'","\""))
            imagePosition = [imagePositionObject['x1'],imagePositionObject['x2'],imagePositionObject['y1'],imagePositionObject['y2']]
            addNewImageToPage(docID,row['pages.id'], imgID,imagePosition)
            newImage = True
        else:
            newImage = False
    
    return createResultDocument(docID, metadata, len(df3.index), len(df3.groupby(['pages.images.id'])))

def drawBox(image, box, color):
    start_point = (int(box[0]), int(box[1]))
    end_point = (int(box[2]), int(box[3]))
    thickness = 3
    draw=ImageDraw.Draw(image)
    draw.rectangle([start_point,end_point],outline=color,width=thickness)
    return image
    #color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    #return cv2.rectangle(image, start_point, end_point, color, thickness)


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
    outputPagePath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"pages",pageID, "jpg")
    imagePath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docID,"images",imageID, "jpg")
    if os.path.isfile(outputPagePath):
        pagePath = outputPagePath
    page = Image.open(pagePath)
    image = Image.open(imagePath)
    tempPage = page.copy()
    tempPage.paste(image, (int(position[0]), int(position[1]), int(position[2]), int(position[3])))
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
    cfg.merge_from_list(['MODEL.WEIGHTS', 'models/model_image_detection.pth', 'MODEL.DEVICE', 'cpu'])
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
    cfg.freeze()
    return cfg

def setup_cfg_OD_Model():
    cfg = get_cfg()
    cfg.merge_from_file("configs/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.WEIGHTS = "models/model_object_detection.pkl"
    cfg.MODEL.DEVICE = "cpu"
    return cfg

def setup_cfg_CHT_Model():
    cfg = get_cfg()
    #cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml"))
    cfg.merge_from_file("configs/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml")
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 4 
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.90
    #cfg.DATASETS.TEST = ("my_dataset_test", )
    cfg.MODEL.WEIGHTS = "models/model_chart_detection.pth"
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
        try:
            creator= ['Creator'].decode("utf-8") 
        except:
            pass
    if 'Producer' in docInfo:
        try:
            producer=doc.info[0]['Producer'].decode("utf-8")
        except:
            pass
    if 'Title' in docInfo:
        try:
            title=doc.info[0]['Title'].decode("utf-8")
        except:
            pass
    if 'Keywords' in docInfo:
        try:
            keywords= doc.info[0]['Keywords'].decode("utf-8")
        except:
            pass
    if 'CreationDate' in docInfo:
        try:
            creationDate=doc.info[0]['CreationDate'].decode("utf-8")
        except:
            pass
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

def metadataFolderStructure(metadataDir):
    projectPath = os.path.abspath(os.path.dirname(__name__))
    if not os.path.exists(os.path.join(projectPath, metadataDir)):
        os.makedirs(os.path.join(projectPath, metadataDir))