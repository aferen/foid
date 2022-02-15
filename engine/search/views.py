from django.shortcuts import render

from rest_framework import status
from .serializers import DocumentSerializer
from .models import Documents, SearchHistory
from .metadata import DocumentDTO, PageDTO, ImageDTO, ObjectDTO, ComplexEncoder, NumpyEncoder
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1

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

from pdf2image import convert_from_path
from detectron2.config import get_cfg
from detectron2.data.detection_utils import read_image
from detectron2.utils.logger import setup_logger
from detectron2.data.detection_utils import convert_PIL_to_numpy

from .detection import ObjectDetection
from .predictor import VisualizationDemo
from detectron2.data import MetadataCatalog

WINDOW_NAME = "COCO detections"
logger = setup_logger()
MetadataCatalog.get("dla_val").thing_classes = ['text', 'title', 'list', 'table', 'figure']



@api_view(['POST'])
def search(request):
    if request.method == 'POST':
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            docID = request.data['docID']
            document = Documents.objects.get(Q(docID=docID))
            if document:
                searchHistory = SearchHistory.objects.filter(Q(document=document)).order_by('pk').last()
                docPath = document.path
                find(docID,docPath)
                query = searchHistory.query
                serializer = DocumentSerializer(document)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def find(docID,docPath):
    mp.set_start_method("spawn", force=True)  
    logger.info("Document Path: " + docPath)
    cfg_DLA_Model = setup_cfg_DLA_Model()
    demo = VisualizationDemo(cfg_DLA_Model)
    outputDir = "%s/%s" % ("media/output",docID)
    inputs = [docPath]
    if len(inputs) == 1:
        inputs = glob.glob(os.path.expanduser(inputs[0]))
        assert inputs, "The input path(s) was not found"

    for path in tqdm.tqdm(inputs, disable=not outputDir): # TODO: for olmalı mı?
        prepareFolderStructure(outputDir)
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
    metadataPath= "%s/%s.%s" % ("media/metadata",metadata_id, ".json")
    with open(metadataPath, 'w') as f:
        f.write(json_data)

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
            image = ImageDTO(img_id,boxes.tensor[index].numpy(),scores[index].numpy(),crop_img.width,crop_img.height)
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
        object=ObjectDTO(obj_id,className[item],boxes.tensor[index].numpy(),scores[index].numpy())
        image.addObject(object)

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