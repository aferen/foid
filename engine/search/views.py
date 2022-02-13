from django.shortcuts import render

from rest_framework import status
from .serializers import DocumentSerializer
from .models import Documents, SearchHistory
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

import argparse
import glob
import multiprocessing as mp
import os
import time
import numpy as np
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

MetadataCatalog.get("dla_val").thing_classes = ['text', 'title', 'list', 'table', 'figure']

WINDOW_NAME = "COCO detections"
datas=[]
objDatas=[]

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
                findObject(docID,docPath)
                query = searchHistory.query
                serializer = DocumentSerializer(document)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def findObject(docID,docPath):
    mp.set_start_method("spawn", force=True)
    logger = setup_logger()
    logger.info("Document Path: " + docPath)
    cfg = setup_cfg()
    demo = VisualizationDemo(cfg)
    outputDir = "%s/%s" % ("media/output",docID)
    inputs = [docPath]
    if len(inputs) == 1:
        inputs = glob.glob(os.path.expanduser(inputs[0]))
        assert inputs, "The input path(s) was not found"

    for path in tqdm.tqdm(inputs, disable=not outputDir):
        projectPath = os.path.abspath(os.path.dirname(__name__))
        if os.path.exists(os.path.join(projectPath, outputDir)):
            shutil.rmtree(os.path.join(projectPath, outputDir))
        pagesPath = "%s/%s" % (outputDir,"pages")
        imagesPath = "%s/%s" % (outputDir,"images")
        os.makedirs(os.path.join(projectPath, pagesPath))
        os.makedirs(os.path.join(projectPath, imagesPath))
        fullPath, documentName = os.path.split(path)
        images = convertPdfToPngPerPage(path)
        for page in range(len(images)):
            #Save pages as images in the pdf
            page_id=uuid.uuid4().hex
            page_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"pages",page_id, "jpg")
            images[page].save(page_path)
            #images[i].save('page' + str(i) + '.jpg', 'JPEG')

            img= convert_PIL_to_numpy(images[page], format="BGR")
            #img = read_image(path, format="BGR")
            start_time = time.time()
            #predictions, visualized_output= demo.run_on_image(img)
            predictions = demo.run_on_image(img)

            createMetaData(predictions, images[page], docID, documentName, page+1, demo)
            logger.info(
                "{} , page {} :  detected {} instances in {:.2f}s".format(
                    path,page+1, len(predictions["instances"]), time.time() - start_time
                )
            )

    json_data = json.dumps(datas,cls=NumpyEncoder)
    metadata_id=uuid.uuid4().hex
    metadataPath= "%s/%s.%s" % ("media/metadata",metadata_id, ".json")
    with open(metadataPath, 'w') as f:
        f.write(json_data)

def createMetaData(predictions, image, docID, documentName, page, demo):
    objectDetection = ObjectDetection()
    predictions = predictions["instances"].to(demo.cpu_device)
    boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
    scores = predictions.scores if predictions.has("scores") else None
    classes = predictions.pred_classes.tolist() if predictions.has("pred_classes") else None

    for index, item in enumerate(classes):
        if item == 4:
            data = {}
            obj={}
            box = list(boxes)[index].detach().cpu().numpy()
            # Crop the PIL image using predicted box coordinates
            img_id=uuid.uuid4().hex
            crop_img = crop_object(image, box)
            #img_path = "media/output/{}.jpg".format(img_id)
            img_path = "%s/%s/%s/%s.%s" % ("media/output",docID,"images",img_id, "jpg")
            crop_img.save(img_path)
            result,className=objectDetection.detect(img_path)
            #objBoxes=result.pred_boxes if result.has("pred_boxes") else None
            #objScores=result.scores if result.has("scores") else None
            objClasses=result.pred_classes.tolist() if result.has("pred_classes") else None
            objLabels=list(map(lambda x: className[x], objClasses))

            """
            obj['boxes']=objBoxes
            obj['scores'] = objScores
            obj['classes'] = objClasses
            obj['lables'] = objLabels
            """


            """
            print("pdf name: ",documentName)
            print("page: ",page)
            print("image id : ",img_id)
            print("position : " ,boxes.tensor[index].numpy())
            print("score : ",scores[index].numpy())
            print("width:",crop_img.width,"px")
            print("height:",crop_img.height,"px")
            """
            data['pdfName'] = documentName
            data['page'] = page
            data['image_id'] = str(img_id)
            data['position'] = boxes.tensor[index].numpy()
            data['score'] = scores[index].numpy()
            data['width'] = crop_img.width
            data['height'] = crop_img.height
            data['objects']= objLabels
            datas.append(data)


def crop_object(image, box):
  """Crops an object in an image

  Inputs:
    image: PIL image
    box: one box from Detectron2 pred_boxes
  """

  x_top_left = box[0]
  y_top_left = box[1]
  x_bottom_right = box[2]
  y_bottom_right = box[3]
  x_center = (x_top_left + x_bottom_right) / 2
  y_center = (y_top_left + y_bottom_right) / 2

  crop_img = image.crop((int(x_top_left), int(y_top_left), int(x_bottom_right), int(y_bottom_right)))

  return crop_img

def setup_cfg():
    cfg = get_cfg()
    cfg.merge_from_file("configs/DLA_mask_rcnn_X_101_32x8d_FPN_3x.yaml")
    cfg.merge_from_list(['MODEL.WEIGHTS', 'models/model_final_trimmed.pth', 'MODEL.DEVICE', 'cpu'])
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = 0.5
    cfg.freeze()
    return cfg

def convertPdfToPngPerPage(pdfPath):
    images = convert_from_path(pdfPath)
    return images

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)